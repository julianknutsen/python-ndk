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

from ndk import serialize


@pytest.fixture()
def fake_repo(ev_repo):
    return ev_repo


@pytest.fixture()
def real_repo(relay_ev_repo):
    return relay_ev_repo


@pytest.fixture(params=["fake_repo", "real_repo"])
def repo(request):
    return request.getfixturevalue(request.param)


# XXX only on fake due to server bug
async def test_empty_object_as_message_returns_notice(
    fake_repo, protocol_rq, protocol_wq, caplog  # pylint: disable=unused-argument
):
    await protocol_wq.put(serialize.serialize_as_str({}))

    await protocol_wq.join()
    await protocol_rq.join()

    assert "Unable to parse message" in caplog.text


# XXX only on fake due to server bug
# @pytest.mark.skip("hangs on recv")
async def test_empty_array_as_message_returns_notice(
    fake_repo, protocol_rq, protocol_wq, caplog  # pylint: disable=unused-argument
):
    await protocol_wq.put(serialize.serialize_as_str([]))

    await protocol_wq.join()
    await protocol_rq.join()

    assert "Unable to parse message" in caplog.text


async def test_only_type_returns_notice(
    fake_repo, protocol_rq, protocol_wq, caplog
):  # pylint: disable=unused-argument
    await protocol_wq.put(
        serialize.serialize_as_str(
            [
                "EVENT",
            ]
        )
    )

    await protocol_wq.join()
    await protocol_rq.join()

    assert "Unable to parse message" in caplog.text
