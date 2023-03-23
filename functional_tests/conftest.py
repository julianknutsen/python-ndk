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

# pylint: disable=redefined-outer-name

import asyncio

import pytest
import websockets

from ndk.repos.event_repo import protocol_handler, relay_event_repo
from server import event_repo, message_dispatcher, message_handler, server


@pytest.fixture(scope="session")
def relay_url(pytestconfig):
    url = pytestconfig.option.relay_url

    if not url:
        pytest.skip()

    return url


@pytest.fixture(scope="function")
async def protocol_rq():
    return asyncio.Queue()


@pytest.fixture(scope="function")
async def protocol_wq():
    return asyncio.Queue()


@pytest.fixture(scope="function")
async def protocol(protocol_rq, protocol_wq):
    ph = protocol_handler.ProtocolHandler(protocol_rq, protocol_wq)
    protocol_read_loop = asyncio.create_task(ph.start_read_loop())
    yield ph
    await ph.stop_read_thread()
    await protocol_read_loop


@pytest.fixture(scope="function")
async def ws_protocol(relay_url, protocol, protocol_rq, protocol_wq):
    ws = await websockets.connect(relay_url)

    reader_task = asyncio.create_task(protocol_handler.read_handler(ws, protocol_rq))
    writer_task = asyncio.create_task(protocol_handler.write_handler(ws, protocol_wq))

    yield protocol

    for task in [reader_task, writer_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    await ws.close()


@pytest.fixture(scope="function")
async def relay_ev_repo(ws_protocol):
    yield relay_event_repo.RelayEventRepo(ws_protocol)


@pytest.fixture(scope="function")
async def ev_repo(protocol, protocol_wq, protocol_rq):
    repo = event_repo.EventRepo()
    msg_handler = message_handler.MessageHandler(repo)
    md = message_dispatcher.MessageDispatcher(msg_handler)
    handler_task = asyncio.create_task(
        server.connection_handler(protocol_wq, protocol_rq, md)
    )  # intentionally swapped
    yield relay_event_repo.RelayEventRepo(protocol)

    handler_task.cancel()
    try:
        await handler_task
    except asyncio.CancelledError:
        pass
