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

import pytest

from ndk import crypto
from ndk.event import event
from ndk.event import parameterized_replaceable_event as pre
from spec_tests import utils


@pytest.fixture
def local(local_relay):
    yield


@pytest.fixture
def remote(remote_relay):
    yield


@pytest.fixture(params=["local", "remote"])
def ctx(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def keys():
    return crypto.KeyPair()


@pytest.fixture
def ev(keys):
    return event.EphemeralEvent.build(keys, kind=20000)


@pytest.mark.usefixtures("ctx")
async def test_paramterized_replaceable_event_no_tag(
    keys, request_queue, response_queue
):
    ev = pre.ParameterizedReplaceableEvent.build(keys, kind=30000, created_at=1)
    await utils.send_and_expect_command_result(ev, request_queue, response_queue)

    replacement = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, content="foo", created_at=2
    )
    await utils.send_and_expect_command_result(
        replacement, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "kinds": [30000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    stored_ev = await utils.expect_relay_event_of_type(
        pre.ParameterizedReplaceableEvent, response_queue
    )
    assert stored_ev == replacement
    await utils.expect_eose(response_queue)
