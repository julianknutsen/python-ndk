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
import functools
import http
import logging
import os
import signal

from websockets.legacy.server import serve

from ndk.repos.event_repo import protocol_handler
from relay import message_dispatcher, message_handler, subscription_handler
from relay.event_repo import event_repo, memory_event_repo, postgres_event_repo

logger = logging.getLogger(__name__)

RELAY_EVENT_REPO = os.environ.get("RELAY_EVENT_REPO", "memory").lower()
HOST = os.environ.get("RELAY_HOST", "localhost")
PORT = int(os.environ.get("RELAY_PORT", "2700"))
DEBUG_LEVEL = os.environ.get("RELAY_LOG_LEVEL", "INFO")

if RELAY_EVENT_REPO == "postgres":
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

logging.basicConfig(level=DEBUG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")


async def connection_handler(
    read_queue: asyncio.Queue[str],
    write_queue: asyncio.Queue[str],
    md: message_dispatcher.MessageDispatcher,
):
    while True:
        data = await read_queue.get()
        read_queue.task_done()
        responses = await md.process_message(data)
        for response in responses:
            await write_queue.put(response)


async def handler_wrapper(repo: event_repo.EventRepo, websocket):
    logger.debug("New connection established from: %s", websocket.remote_address)
    request_queue: asyncio.Queue[str] = asyncio.Queue()
    response_queue: asyncio.Queue[str] = asyncio.Queue()

    sh = subscription_handler.SubscriptionHandler(response_queue)
    mh = message_handler.MessageHandler(repo, sh)
    md = message_dispatcher.MessageDispatcher(mh)
    repo.register_insert_cb(sh.handle_event)

    # XXX: Need to clean these up
    asyncio.create_task(protocol_handler.read_handler(websocket, request_queue))
    asyncio.create_task(protocol_handler.write_handler(websocket, response_queue))

    return await connection_handler(request_queue, response_queue, md)


async def health_check(path, _):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"


async def main():
    logger.info("Logging set to %s", DEBUG_LEVEL)

    if RELAY_EVENT_REPO == "memory":
        repo = memory_event_repo.MemoryEventRepo()
    elif RELAY_EVENT_REPO == "postgres":
        repo = await postgres_event_repo.PostgresEventRepo.create(
            DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
        )
    else:
        raise ValueError(f"Unknown event repo: {RELAY_EVENT_REPO}")
    logger.debug("%s initialized", repo.__class__)

    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with serve(
        functools.partial(handler_wrapper, repo),
        HOST,
        PORT,
        process_request=health_check,
    ):
        await stop


if __name__ == "__main__":
    asyncio.run(main())
