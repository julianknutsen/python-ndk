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
from ndk.event import (
    contact_list_event,
    event_builder,
    event_tags,
    metadata_event,
    text_note_event,
)
from ndk.messages import command_result, event_message, message_factory, relay_event
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
def signed_event(keys):
    return text_note_event.TextNoteEvent.from_content(keys, "Hello, world!")


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_id(signed_event, request_queue, response_queue):
    cmd_result = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_two_inserts_one_result(
    signed_event, request_queue, response_queue
):
    cmd_result1 = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )
    cmd_result2 = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )
    assert cmd_result1.event_id == cmd_result2.event_id

    fltr = {"ids": [cmd_result1.event_id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_author(request_queue, response_queue, signed_event):
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_id_and_author(
    request_queue, response_queue, signed_event
):
    cmd_result = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"ids": [cmd_result.event_id], "authors": [signed_event.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_wrong_id_and_author_returns_empty(
    request_queue, response_queue, signed_event
):
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"ids": [signed_event.pubkey], "authors": [signed_event.pubkey]}  # wrong id

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_kind(request_queue, response_queue, signed_event):
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "kinds": [1]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_limit_respected_returns_newest(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed_event1 = text_note_event.TextNoteEvent.from_content(
            keys, "Hello, world!"
        )

    with mock.patch("time.time", return_value=cur + 1):
        signed_event2 = text_note_event.TextNoteEvent.from_content(
            keys, "Hello, world, later!"
        )

    await utils.send_and_expect_command_result(
        signed_event1, request_queue, response_queue
    )
    await utils.send_and_expect_command_result(
        signed_event2, request_queue, response_queue
    )

    fltr = {"authors": [signed_event1.pubkey], "limit": 1}

    await utils.send_req_with_filter("1", [fltr], request_queue)

    relay_signed = await utils.expect_text_note_event(response_queue)
    assert relay_signed == signed_event2  # second insert is returned

    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_since_equal_cur_no_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed_event = text_note_event.TextNoteEvent.from_content(keys, "Hello, world!")

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "since": cur}  # (since,]

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_since_less_cur_has_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed_event = text_note_event.TextNoteEvent.from_content(keys, "Hello, world!")

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "since": cur - 1}  # (since,]

    await utils.send_req_with_filter("1", [fltr], request_queue)

    relay_signed = await utils.expect_text_note_event(response_queue)
    assert relay_signed == signed_event

    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_until_equal_cur_no_result(
    request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed_event = text_note_event.TextNoteEvent.from_content(keys, "Hello, world!")

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "since": cur}  # (, until)

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_author_until_less_cur_has_result(
    request_queue, response_queue
):
    keys = crypto.KeyPair()

    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed_event = text_note_event.TextNoteEvent.from_content(keys, "Hello, world!")

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "since": cur - 1}  # (, until)

    await utils.send_req_with_filter("1", [fltr], request_queue)

    relay_signed = await utils.expect_text_note_event(response_queue)
    assert relay_signed == signed_event

    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_no_tag_inserted(
    request_queue, response_queue, signed_event
):
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)


def build_with_tags(keys, tags=None):
    if not tags:
        tags = []

    return text_note_event.TextNoteEvent.from_content(
        keys, "Hello, world!", tags=event_tags.EventTags(tags)
    )


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_ptag(request_queue, response_queue, keys):
    signed_event = build_with_tags(keys, tags=[["p", keys.public]])

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_ptag_with_relay(
    request_queue, response_queue, keys
):
    signed_event = build_with_tags(
        keys, tags=[["p", keys.public, "ws://relay.example.com"]]
    )

    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "#p": [signed_event.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_multiple_ptag_in_event(
    request_queue, response_queue, keys
):
    keys2 = crypto.KeyPair()
    signed_event = build_with_tags(keys, tags=[["p", keys.public], ["p", keys2.public]])
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "#p": [keys.public]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)

    fltr = {"authors": [keys.public], "#p": [keys2.public]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_multiple_ptag_in_filter(
    request_queue, response_queue, keys
):
    signed_event = build_with_tags(
        keys, tags=[["p", keys.public, "ws://relay.example.com"]]
    )
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    keys2 = crypto.KeyPair()
    signed_event2 = build_with_tags(keys, tags=[["p", keys2.public]])
    await utils.send_and_expect_command_result(
        signed_event2, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "#p": [keys.public, keys2.public]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_etag(
    request_queue, response_queue, keys, signed_event
):
    cmd_result = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    signed_event2 = build_with_tags(keys, tags=[["e", cmd_result.event_id]])

    await utils.send_and_expect_command_result(
        signed_event2, request_queue, response_queue
    )

    fltr = {"authors": [signed_event.pubkey], "#e": [signed_event.id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    relay_event = await utils.expect_text_note_event(response_queue)
    assert relay_event == signed_event2
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_find_by_tag_etag_and_ptag(
    request_queue, response_queue, keys, signed_event
):
    cmd_result = await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )

    signed_event2 = build_with_tags(
        keys, tags=[["e", cmd_result.event_id], ["p", keys.public]]
    )

    await utils.send_and_expect_command_result(
        signed_event2, request_queue, response_queue
    )

    fltr = {
        "authors": [signed_event.pubkey],
        "#e": [signed_event.id],
        "#p": [signed_event2.pubkey],
    }

    await utils.send_req_with_filter("1", [fltr], request_queue)
    relay_event = await utils.expect_text_note_event(response_queue)
    assert relay_event == signed_event2
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_multiple_filters_or(
    request_queue, response_queue, keys, signed_event
):
    await utils.send_and_expect_command_result(
        signed_event, request_queue, response_queue
    )
    keys2 = crypto.KeyPair()
    signed_event2 = build_with_tags(keys2)
    await utils.send_and_expect_command_result(
        signed_event2, request_queue, response_queue
    )

    fltr1 = {
        "authors": [keys.public],
    }
    fltr2 = {
        "authors": [keys2.public],
    }
    await utils.send_req_with_filter("1", [fltr1, fltr2], request_queue)

    await utils.expect_text_note_event(response_queue)
    await utils.expect_text_note_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_receive_event_from_sub(
    request_queue, response_queue, keys, signed_event
):
    fltr = {
        "authors": [keys.public],
    }
    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )

    # due to the ordering of the db commit cb, the sub response may arrive
    # before the command result

    msg = message_factory.from_str(await response_queue.get())
    if isinstance(msg, command_result.CommandResult):
        await utils.expect_text_note_event(response_queue)
    else:
        await utils.expect_successful_command_result(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_text_note_receive_two_events_from_two_subs(
    request_queue, response_queue, keys, signed_event
):
    fltr = {
        "authors": [keys.public],
    }
    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await utils.send_req_with_filter("2", [fltr], request_queue)
    await utils.expect_eose(response_queue)

    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )

    # due to the ordering of the db commit cb, the sub response may
    # arrive before the command result
    msgs = []
    msgs.append(message_factory.from_str(await response_queue.get()))
    msgs.append(message_factory.from_str(await response_queue.get()))
    msgs.append(message_factory.from_str(await response_queue.get()))

    remaining_cmd_result = 1
    remaining_relay_event_subs = set(["1", "2"])
    for msg in msgs:
        if isinstance(msg, command_result.CommandResult):
            assert remaining_cmd_result > 0
            remaining_cmd_result -= 1
        else:
            assert isinstance(msg, relay_event.RelayEvent)
            remaining_relay_event_subs.remove(msg.sub_id)


@pytest.mark.parametrize(
    "signed_builder",
    [
        contact_list_event.ContactListEvent.from_contact_list,
        metadata_event.MetadataEvent.from_metadata_parts,
    ],
)
@pytest.mark.usefixtures("ctx")
async def test_second_event_delete_previous(
    signed_builder, request_queue, response_queue, keys
):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        signed = signed_builder(keys)

    cur = int(time.time())
    with mock.patch("time.time", return_value=cur + 1):
        signed2 = signed_builder(keys)

    await utils.send_and_expect_command_result(signed, request_queue, response_queue)
    await utils.send_and_expect_command_result(signed2, request_queue, response_queue)

    fltr = {"authors": [keys.public]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.send_close("1", request_queue)

    relay_signed = event_builder.from_dict(
        (await utils.expect_relay_event(response_queue)).event_dict
    )
    assert relay_signed == signed2
    await utils.expect_eose(response_queue)
