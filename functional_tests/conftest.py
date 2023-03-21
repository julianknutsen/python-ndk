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


@pytest.fixture(scope="session")
def relay_url(pytestconfig):
    url = pytestconfig.option.relay_url

    if not url:
        pytest.skip()

    return url


@pytest.fixture(scope="function")
async def ws_protocol(relay_url):
    rq = asyncio.Queue()
    wq = asyncio.Queue()
    ws = await websockets.connect(relay_url)

    reader_task = asyncio.create_task(protocol_handler.read_handler(ws, rq))
    writer_task = asyncio.create_task(protocol_handler.write_handler(ws, wq))

    transport = protocol_handler.ProtocolHandler(rq, wq)
    protocol_read_loop = asyncio.create_task(transport.start_read_loop())

    yield transport

    await transport.stop_read_thread()

    _, pending = await asyncio.wait(
        [reader_task, writer_task, protocol_read_loop],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    await ws.close()


@pytest.fixture(scope="function")
async def relay_ev_repo(ws_protocol):
    yield relay_event_repo.RelayEventRepo(ws_protocol)
