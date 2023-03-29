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
from ndk.event import event, event_parser, text_note_event
from ndk.messages import (
    command_result,
    eose,
    event_message,
    message_factory,
    relay_event,
    request,
)


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
def signed_event(keys):
    unsigned_event = text_note_event.TextNoteEvent.from_content("Hello, world!")
    signed_event = event.build_signed_event(unsigned_event, keys)
    return signed_event


async def send_and_expect_command_result(
    signed_event: event.SignedEvent, request_queue, response_queue
) -> command_result.CommandResult:
    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )
    cmd_result = message_factory.from_str(await response_queue.get())
    assert isinstance(cmd_result, command_result.CommandResult)
    assert cmd_result.accepted
    return cmd_result


async def send_req_with_filter(fltrs, request_queue):
    r = request.Request("1", fltrs)
    await request_queue.put(r.serialize())


async def expect_text_note_event(response_queue) -> event.SignedEvent:
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, relay_event.RelayEvent)
    signed = event.SignedEvent.from_dict(msg.event_dict)
    unsigned = event_parser.signed_to_unsigned(signed)
    assert isinstance(unsigned, text_note_event.TextNoteEvent)
    return signed


async def expect_eose(response_queue):
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, eose.EndOfStoredEvents)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_id(signed_event, request_queue, response_queue):
    cmd_result = await send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_author(request_queue, response_queue, signed_event):
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_id_and_author(
    request_queue, response_queue, signed_event
):
    cmd_result = await send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id], "authors": [signed_event.pubkey]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_wrong_id_and_author_returns_empty(
    request_queue, response_queue, signed_event
):
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"ids": [signed_event.pubkey], "authors": [signed_event.pubkey]}  # wrong id

    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_kind(request_queue, response_queue, signed_event):
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "kinds": [1]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_limit_respected_returns_newest(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned_event1 = text_note_event.TextNoteEvent.from_content("Hello, world!")
        signed_event1 = event.build_signed_event(unsigned_event1, keys)

    with mock.patch("time.time", return_value=cur + 1):
        unsigned_event2 = text_note_event.TextNoteEvent.from_content(
            "Hello, world, later!"
        )
        signed_event2 = event.build_signed_event(unsigned_event2, keys)

    await send_and_expect_command_result(signed_event1, request_queue, response_queue)
    await send_and_expect_command_result(signed_event2, request_queue, response_queue)

    fltr = {"authors": [signed_event1.pubkey], "limit": 1}

    await send_req_with_filter([fltr], request_queue)

    relay_signed = await expect_text_note_event(response_queue)
    assert relay_signed == signed_event2  # second insert is returned

    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_since_equal_cur_no_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned_event = text_note_event.TextNoteEvent.from_content("Hello, world!")
        signed_event = event.build_signed_event(unsigned_event, keys)

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "since": cur}  # (since,]

    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_since_less_cur_has_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned_event = text_note_event.TextNoteEvent.from_content("Hello, world!")
        signed_event = event.build_signed_event(unsigned_event, keys)

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [keys.public], "since": cur - 1}  # (since,]

    await send_req_with_filter([fltr], request_queue)

    relay_signed = await expect_text_note_event(response_queue)
    assert relay_signed == signed_event

    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_until_equal_cur_no_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned_event = text_note_event.TextNoteEvent.from_content("Hello, world!")
        signed_event = event.build_signed_event(unsigned_event, keys)

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [keys.public], "since": cur}  # (, until)

    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_until_less_cur_has_result(
    request_queue, response_queue
):
    keys = crypto.KeyPair()

    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned_event = text_note_event.TextNoteEvent.from_content("Hello, world!")
        signed_event = event.build_signed_event(unsigned_event, keys)

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [keys.public], "since": cur - 1}  # (, until)

    await send_req_with_filter([fltr], request_queue)

    relay_signed = await expect_text_note_event(response_queue)
    assert relay_signed == signed_event

    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_no_tag_inserted(
    request_queue, response_queue, signed_event
):
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)


def build_with_tags(keys, tags=None):
    if not tags:
        tags = [[]]

    unsigned_event = text_note_event.TextNoteEvent.from_content(
        "Hello, world!", tags=event.EventTags(tags)
    )
    return event.build_signed_event(unsigned_event, keys)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_ptag(request_queue, response_queue, keys):
    signed_event = build_with_tags(keys, tags=[["p", keys.public]])

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_ptag_with_relay(
    request_queue, response_queue, keys
):
    signed_event = build_with_tags(
        keys, tags=[["p", keys.public, "ws://relay.example.com"]]
    )

    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_multiple_ptag_in_event(
    request_queue, response_queue, keys
):
    keys2 = crypto.KeyPair()
    signed_event = build_with_tags(keys, tags=[["p", keys.public], ["p", keys2.public]])
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    fltr = {"authors": [keys.public], "#p": [keys.public]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)

    fltr = {"authors": [keys.public], "#p": [keys2.public]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_multiple_ptag_in_filter(
    request_queue, response_queue, keys
):
    signed_event = build_with_tags(
        keys, tags=[["p", keys.public, "ws://relay.example.com"]]
    )
    await send_and_expect_command_result(signed_event, request_queue, response_queue)

    keys2 = crypto.KeyPair()
    signed_event2 = build_with_tags(keys, tags=[["p", keys2.public]])
    await send_and_expect_command_result(signed_event2, request_queue, response_queue)

    fltr = {"authors": [keys.public], "#p": [keys.public, keys2.public]}

    await send_req_with_filter([fltr], request_queue)
    await expect_text_note_event(response_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_etag(
    request_queue, response_queue, keys, signed_event
):
    cmd_result = await send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    signed_event2 = build_with_tags(keys, tags=[["e", cmd_result.event_id]])

    await send_and_expect_command_result(signed_event2, request_queue, response_queue)

    fltr = {"authors": [signed_event.pubkey], "#e": [signed_event.id]}

    await send_req_with_filter([fltr], request_queue)
    relay_event = await expect_text_note_event(response_queue)
    assert relay_event == signed_event2
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_etag_and_ptag(
    request_queue, response_queue, keys, signed_event
):
    cmd_result = await send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    signed_event2 = build_with_tags(
        keys, tags=[["e", cmd_result.event_id], ["p", keys.public]]
    )

    await send_and_expect_command_result(signed_event2, request_queue, response_queue)

    fltr = {
        "authors": [signed_event.pubkey],
        "#e": [signed_event.id],
        "#p": [signed_event2.pubkey],
    }

    await send_req_with_filter([fltr], request_queue)
    relay_event = await expect_text_note_event(response_queue)
    assert relay_event == signed_event2
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_multiple_filters_or(
    request_queue, response_queue, keys, signed_event
):
    await send_and_expect_command_result(signed_event, request_queue, response_queue)
    keys2 = crypto.KeyPair()
    signed_event2 = build_with_tags(keys2)
    await send_and_expect_command_result(signed_event2, request_queue, response_queue)

    fltr1 = {
        "authors": [keys.public],
    }
    fltr2 = {
        "authors": [keys2.public],
    }
    await send_req_with_filter([fltr1, fltr2], request_queue)

    await expect_text_note_event(response_queue)
    await expect_text_note_event(response_queue)
    await expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_receive_event_from_sub(
    request_queue, response_queue, keys, signed_event
):
    fltr = {
        "authors": [keys.public],
    }
    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)

    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )

    # due to the ordering of the db commit, the sub response will arrive
    # before the command result
    await expect_text_note_event(response_queue)
    cmd_result = message_factory.from_str(await response_queue.get())

    assert isinstance(cmd_result, command_result.CommandResult)
    assert cmd_result.accepted
    return cmd_result


@pytest.mark.usefixtures("ctx")
async def test_text_note_receive_two_events_from_two_subs(
    request_queue, response_queue, keys, signed_event
):
    fltr = {
        "authors": [keys.public],
    }
    await send_req_with_filter([fltr], request_queue)
    await expect_eose(response_queue)

    r = request.Request("2", [fltr])
    await request_queue.put(r.serialize())
    await expect_eose(response_queue)

    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )

    # due to the ordering of the db commit, the sub response will arrive
    # before the command result
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, relay_event.RelayEvent)
    assert msg.sub_id == "1"

    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, relay_event.RelayEvent)
    assert msg.sub_id == "2"

    cmd_result = message_factory.from_str(await response_queue.get())
    assert isinstance(cmd_result, command_result.CommandResult)
    assert cmd_result.accepted
    return cmd_result
