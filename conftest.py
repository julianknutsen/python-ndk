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
# pylint: disable=redefined-outer-name, unused-argument

import asyncio

import pytest
import websockets

from ndk.repos.event_repo import protocol_handler, relay_event_repo
from relay import (
    event_handler,
    message_dispatcher,
    message_handler,
    server,
    subscription_handler,
)
from relay.event_repo import memory_event_repo


def pytest_addoption(parser):
    parser.addoption(
        "--relay-url",
        action="store",
        default=None,
        help="The URL of the relay server to test",
    )
    parser.addoption(
        "--db-url",
        action="store",
        default=None,
        help="The URL of the relay server to test",
    )


@pytest.fixture(scope="session")
def relay_url(pytestconfig):
    url = pytestconfig.option.relay_url

    if not url:
        pytest.skip()

    return url


@pytest.fixture(scope="session")
def db_url(pytestconfig):
    url = pytestconfig.option.db_url

    if not url:
        pytest.skip()

    return url


@pytest.fixture(scope="function")
async def response_queue():
    return asyncio.Queue()


@pytest.fixture(scope="function")
async def request_queue():
    return asyncio.Queue()


@pytest.fixture(scope="function")
async def protocol(response_queue, request_queue):
    ph = protocol_handler.ProtocolHandler(response_queue, request_queue)
    protocol_read_loop = asyncio.create_task(ph.start_read_loop())
    yield ph
    await ph.stop_read_thread()
    await protocol_read_loop


@pytest.fixture(scope="function")
async def ws(relay_url):
    ws = await websockets.connect(relay_url)
    yield ws
    await ws.close()


@pytest.fixture(scope="function")
async def ws_handlers(ws, request_queue, response_queue):
    reader_task = asyncio.create_task(protocol_handler.read_handler(ws, response_queue))
    writer_task = asyncio.create_task(protocol_handler.write_handler(ws, request_queue))

    yield

    for task in [reader_task, writer_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.fixture(scope="function")
async def remote_relay(ws_handlers):
    yield


@pytest.fixture(scope="function")
async def local_relay(response_queue, request_queue):
    sh = subscription_handler.SubscriptionHandler(response_queue)
    repo = memory_event_repo.MemoryEventRepo()
    eh = event_handler.EventHandler(repo)
    msg_handler = message_handler.MessageHandler(repo, sh, eh)
    md = message_dispatcher.MessageDispatcher(msg_handler)
    repo.register_insert_cb(sh.handle_event)

    handler_task = asyncio.create_task(
        server.connection_handler(request_queue, response_queue, md)
    )  # intentionally swapped

    yield

    handler_task.cancel()
    try:
        await handler_task
    except asyncio.CancelledError:
        pass


@pytest.fixture(scope="function")
async def ev_repo(protocol):
    return relay_event_repo.RelayEventRepo(protocol)
