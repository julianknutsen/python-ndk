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

from websockets import exceptions as websockets_exceptions

from ndk import crypto, exceptions, types
from ndk.event import auth_event, event, event_filter, stored_events
from ndk.messages import (
    auth,
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
logger.propagate = True


async def read_handler(websocket, read_queue: asyncio.Queue):
    while True:
        try:
            data = await websocket.recv()
        except websockets_exceptions.ConnectionClosed:
            break
        logger.debug("Read: %s", data)
        await read_queue.put(data)


async def write_handler(websocket, write_queue: asyncio.Queue):
    while True:
        data = await write_queue.get()
        write_queue.task_done()
        logger.debug("Sending: %s", data)
        try:
            await websocket.send(data)
        except websockets_exceptions.ConnectionClosed:
            break


class ProtocolHandler:
    _keys: typing.Optional[crypto.KeyPair]
    _relay_url: typing.Optional[str]
    _write_waiters: dict[types.EventID, asyncio.Future]
    _read_waiters: dict[str, asyncio.Queue[message.Message]]
    _read_queue: asyncio.Queue
    _write_queue: asyncio.Queue
    _stop: asyncio.Event

    def __init__(
        self,
        keys: typing.Optional[crypto.KeyPair],
        relay_url: typing.Optional[str],
        read_queue: asyncio.Queue,
        write_queue: asyncio.Queue,
    ):
        self._keys = keys
        self._relay_url = relay_url
        self._read_queue = read_queue
        self._write_queue = write_queue
        self._stop = asyncio.Event()
        self._read_waiters = {}
        self._write_waiters = {}

    async def stop_read_thread(self):
        logger.debug("Received signal to stop read loop")
        self._stop.set()

    async def _process_data(self, data: str):
        try:
            msg = message_factory.from_str(data)
        except exceptions.ParseError as exc:
            logger.error("Error parsing from read queue: %s", exc)
            return

        if isinstance(msg, notice.Notice):
            logger.error("%s", msg)

        elif isinstance(msg, command_result.CommandResult):
            self._write_waiters[types.EventID(msg.event_id)].set_result(msg)

        elif isinstance(msg, (relay_event.RelayEvent, eose.EndOfStoredEvents)):
            if msg.sub_id not in self._read_waiters:
                logger.error(
                    "Dropping received message for sub_id that was never initiated: %s",
                    msg,
                )
                return

            await self._read_waiters[msg.sub_id].put(msg)

        elif isinstance(msg, auth.AuthRequest):
            if self._keys is None:
                logger.warning("Authentication not supported. Did you provide a key?")
            else:
                assert self._relay_url
                assert self._keys
                challenge_ev = auth_event.AuthEvent.from_parts(
                    self._keys, self._relay_url, msg.challenge
                )
                challenge_resp = auth.AuthResponse(challenge_ev)
                await self._write_queue.put(challenge_resp.serialize())

    async def start_read_loop(self):
        logger.debug("Read loop starting")
        while not self._stop.is_set():
            try:
                data = await asyncio.wait_for(self._read_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # enable reading of stop event
            else:
                try:
                    await self._process_data(data)
                finally:
                    self._read_queue.task_done()

        logger.debug("Read loop ending")

    async def write_event(self, ev: event.Event) -> command_result.CommandResult:
        awaitable: asyncio.Future[command_result.CommandResult] = asyncio.Future()
        await self._write_queue.put(event_message.Event.from_event(ev).serialize())
        self._write_waiters[ev.id] = awaitable

        return await asyncio.wait_for(awaitable, timeout=10.0)

    async def query_events(
        self, fltrs: list[event_filter.EventFilter]
    ) -> typing.Sequence[event.Event]:
        # logger.debug("query_events(%s)", fltrs)
        sub_id = str(uuid.uuid4())
        req = request.Request(sub_id, [fltr.for_req() for fltr in fltrs])

        stored = stored_events.StoredEvents()

        awaitable: asyncio.Queue[message.Message] = asyncio.Queue()
        await self._write_queue.put(req.serialize())

        assert sub_id not in self._read_waiters
        self._read_waiters[sub_id] = awaitable

        while not stored.process_msg(
            await asyncio.wait_for(awaitable.get(), timeout=10.0)
        ):
            awaitable.task_done()
            continue

        serialized = close.Close(sub_id).serialize()
        await self._write_queue.put(serialized)
        del self._read_waiters[sub_id]

        return stored.get()
