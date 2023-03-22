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
import logging

from websockets.legacy.server import serve

from ndk.repos.event_repo import protocol_handler
from server import event_repo, message_dispatcher, message_handler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

HOST = "localhost"
PORT = 8765


async def connection_handler(
    read_queue: asyncio.Queue[str],
    write_queue: asyncio.Queue[str],
    mh: message_dispatcher.MessageDispatcher,
):
    while True:
        data = await read_queue.get()
        read_queue.task_done()
        responses = mh.process_message(data)
        for response in responses:
            await write_queue.put(response)


async def handler_wrapper(mh: message_dispatcher.MessageDispatcher, websocket):
    logger.debug("New connection established from: %s", websocket.remote_address)
    rq: asyncio.Queue[str] = asyncio.Queue()
    wq: asyncio.Queue[str] = asyncio.Queue()

    # XXX: Need to clean these up
    asyncio.create_task(protocol_handler.read_handler(websocket, rq))
    asyncio.create_task(protocol_handler.write_handler(websocket, wq))

    return await connection_handler(rq, wq, mh)


async def main():
    repo = event_repo.EventRepo()
    mh = message_handler.MessageHandler(repo)
    mb = message_dispatcher.MessageDispatcher(mh)

    async with serve(functools.partial(handler_wrapper, mb), HOST, PORT):
        logger.info("Listening on %s:%s", HOST, PORT)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
