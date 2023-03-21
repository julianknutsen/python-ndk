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

import pytest
import websockets

from ndk import serialize
from ndk.messages import message_factory, notice


@pytest.fixture()
async def ws(relay_url):
    tmp = await websockets.connect(relay_url)
    yield tmp
    await tmp.close()


@pytest.mark.skip("hangs on recv")
async def test_empty_object_as_message_returns_notice(ws):
    await ws.send(serialize.serialize_as_str("{}"))

    msg = message_factory.from_str(await ws.recv())
    assert isinstance(msg, notice.Notice)


@pytest.mark.skip("hangs on recv")
async def test_empty_array_as_message_returns_notice(ws):
    await ws.send(serialize.serialize_as_str("[]"))

    msg = message_factory.from_str(await ws.recv())
    assert isinstance(msg, notice.Notice)


async def test_only_type_returns_notice(ws):
    await ws.send(
        serialize.serialize_as_str(
            [
                "EVENT",
            ]
        )
    )

    msg = message_factory.from_str(await ws.recv())
    assert isinstance(msg, notice.Notice)
