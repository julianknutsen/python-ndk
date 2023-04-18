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

import time

import mock
import pytest

from ndk import crypto
from ndk.event import event
from ndk.messages import event_message
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
def ephemeral_ev(keys):
    return event.EphemeralEvent.build(keys, kind=20000)


@pytest.fixture
def regular_ev(keys):
    return event.RegularEvent.build(keys, kind=1000)


@pytest.fixture
def replaceable_ev(keys):
    return event.ReplaceableEvent.build(keys, kind=10000)


@pytest.mark.usefixtures("ctx")
async def test_ephemeral_event_not_saved(ephemeral_ev, request_queue, response_queue):
    cmd_result = await utils.send_and_expect_command_result(
        ephemeral_ev, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_ephemeral_event_broadcast(ephemeral_ev, request_queue, response_queue):
    fltr = {"authors": [ephemeral_ev.pubkey], "kind": [20000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await request_queue.put(event_message.Event.from_event(ephemeral_ev).serialize())
    await utils.expect_relay_event_of_type(event.EphemeralEvent, response_queue)
    await utils.expect_successful_command_result(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_regular_event_saved(regular_ev, request_queue, response_queue):
    cmd_result = await utils.send_and_expect_command_result(
        regular_ev, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_relay_event_of_type(event.RegularEvent, response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_regular_event_broadcast(regular_ev, request_queue, response_queue):
    fltr = {"authors": [regular_ev.pubkey], "kind": [1000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await request_queue.put(event_message.Event.from_event(regular_ev).serialize())
    await utils.expect_relay_event_of_type(event.RegularEvent, response_queue)
    await utils.expect_successful_command_result(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_replaceable_event_saved(replaceable_ev, request_queue, response_queue):
    cmd_result = await utils.send_and_expect_command_result(
        replaceable_ev, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_relay_event_of_type(event.ReplaceableEvent, response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_replaceable_event_broadcast(
    replaceable_ev, request_queue, response_queue
):
    fltr = {"authors": [replaceable_ev.pubkey], "kind": [10000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await request_queue.put(event_message.Event.from_event(replaceable_ev).serialize())
    await utils.expect_relay_event_of_type(event.ReplaceableEvent, response_queue)
    await utils.expect_successful_command_result(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_replaceable_event_replaced_by_newer(keys, request_queue, response_queue):
    now = time.time()
    with mock.patch("time.time", return_value=now):
        older_ev = event.ReplaceableEvent.build(keys, kind=10000)

    with mock.patch("time.time", return_value=now + 1):
        newer_ev = event.ReplaceableEvent.build(keys, kind=10000)

    await utils.send_and_expect_command_result(older_ev, request_queue, response_queue)
    await utils.send_and_expect_command_result(newer_ev, request_queue, response_queue)
    fltr = {"authors": [keys.public], "kind": [10000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    ev = await utils.expect_relay_event_of_type(event.ReplaceableEvent, response_queue)
    assert ev == newer_ev
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_replaceable_event_not_replaced_by_older(
    keys, request_queue, response_queue
):
    now = time.time()
    with mock.patch("time.time", return_value=now):
        older_ev = event.ReplaceableEvent.build(keys, kind=10000)

    with mock.patch("time.time", return_value=now + 1):
        newer_ev = event.ReplaceableEvent.build(keys, kind=10000)

    await utils.send_and_expect_command_result(newer_ev, request_queue, response_queue)
    await utils.send_and_expect_command_result(older_ev, request_queue, response_queue)
    fltr = {"authors": [keys.public], "kind": [10000]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    ev = await utils.expect_relay_event_of_type(event.ReplaceableEvent, response_queue)
    assert ev == newer_ev
    await utils.expect_eose(response_queue)
