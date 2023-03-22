# Copyright 2023 Julian Knutsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the “Software”), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import asyncio
import logging
import typing
import uuid

from ndk import exceptions
from ndk.event import event, stored_events
from ndk.messages import (
    close,
    command_result,
    eose,
    event_message,
    message,
    message_factory,
    notice,
    relay_event,
    request,
)

logger = logging.getLogger(__name__)


async def read_handler(websocket, read_queue: asyncio.Queue):
    async for data in websocket:
        logger.debug("Read: %s", data)
        await read_queue.put(data)


async def write_handler(websocket, write_queue: asyncio.Queue):
    while True:
        data = await write_queue.get()
        write_queue.task_done()
        logger.debug("Sending: %s", data)
        await websocket.send(data)


class ProtocolHandler:
    _write_waiters: dict[event.EventID, asyncio.Future]
    _read_waiters: dict[str, asyncio.Queue[message.Message]]
    _read_queue: asyncio.Queue
    _write_queue: asyncio.Queue
    _stop: asyncio.Event

    def __init__(self, read_queue: asyncio.Queue, write_queue: asyncio.Queue):
        self._read_queue = read_queue
        self._write_queue = write_queue
        self._stop = asyncio.Event()
        self._read_waiters = {}
        self._write_waiters = {}

    async def stop_read_thread(self):
        logger.debug("Received signal to stop read loop")
        self._stop.set()

    async def _read_loop_iteration(self):
        try:
            token = await asyncio.wait_for(self._read_queue.get(), timeout=0.1)
            self._read_queue.task_done()
        except asyncio.TimeoutError:
            return  # enable reading of stop event

        try:
            msg = message_factory.from_str(token)
        except exceptions.ParseError as exc:
            logger.error("Error parsing from read queue: %s", exc)
            return

        if isinstance(msg, notice.Notice):
            logger.error("%s", msg)

        elif isinstance(msg, command_result.CommandResult):
            self._write_waiters[event.EventID(msg.event_id)].set_result(msg)

        elif isinstance(msg, (relay_event.RelayEvent, eose.EndOfStoredEvents)):
            if msg.sub_id not in self._read_waiters:
                logger.error(
                    "Dropping received message for sub_id that was never initiated: %s",
                    msg,
                )
                return

            await self._read_waiters[msg.sub_id].put(msg)

    async def start_read_loop(self):
        logger.debug("Read loop starting")
        while not self._stop.is_set():
            await self._read_loop_iteration()
        logger.debug("Read loop ending")

    async def write_event(self, ev: event.SignedEvent) -> command_result.CommandResult:
        awaitable: asyncio.Future[command_result.CommandResult] = asyncio.Future()
        await self._write_queue.put(
            event_message.Event.from_signed_event(ev).serialize()
        )
        self._write_waiters[ev.id] = awaitable

        return await awaitable

    async def query_events(
        self, fltrs: list[dict]
    ) -> typing.Sequence[event.UnsignedEvent]:
        logger.debug("query_events(%s)", fltrs)
        sub_id = str(uuid.uuid4())
        req = request.Request(sub_id, fltrs)

        stored = stored_events.StoredEvents()

        awaitable: asyncio.Queue[message.Message] = asyncio.Queue()
        await self._write_queue.put(req.serialize())

        assert sub_id not in self._read_waiters
        self._read_waiters[sub_id] = awaitable

        while not stored.process_msg(await awaitable.get()):
            awaitable.task_done()
            continue

        serialized = close.Close(sub_id).serialize()
        await self._write_queue.put(serialized)
        del self._read_waiters[sub_id]

        return stored.get()
