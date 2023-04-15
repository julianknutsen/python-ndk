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
import ssl

import pytest
import websockets

from ndk import crypto
from ndk.messages import auth, message_factory
from ndk.relay import (
    auth_handler,
    event_handler,
    event_notifier,
    message_dispatcher,
    message_handler,
    subscription_handler,
)
from ndk.relay.event_repo import memory_event_repo
from ndk.repos.event_repo import protocol_handler, relay_event_repo
from relay import server


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


@pytest.fixture
def keys():
    return crypto.KeyPair()


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
    class UnauthResponseQueue(asyncio.Queue):
        async def get(self):
            data = await super().get()
            try:
                msg = message_factory.from_str(data)
            except ValueError:
                return data

            if isinstance(msg, auth.Auth):
                return await super().get()
            else:
                return data

    return UnauthResponseQueue()


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
    ssl_context = None
    if "wss" in relay_url:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    ws = await websockets.connect(relay_url, ssl=ssl_context)
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
async def local_relay(
    response_queue,
    request_queue,
):
    auth = auth_handler.AuthHandler("wss://in-memory")
    sh = subscription_handler.SubscriptionHandler(response_queue)
    repo = memory_event_repo.MemoryEventRepo()
    ev_notifier = event_notifier.EventNotifier()
    eh = event_handler.EventHandler(auth, repo, ev_notifier)
    msg_handler = message_handler.MessageHandler(repo, sh, eh)
    md = message_dispatcher.MessageDispatcher(msg_handler)
    eh.register_received_cb(sh.handle_event)
    await response_queue.put(auth.build_auth_message())

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
