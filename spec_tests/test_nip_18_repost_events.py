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

from ndk.event import repost_event, text_note_event
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


@pytest.fixture()
def text_note(keys, request_queue, response_queue):
    signed_event = text_note_event.TextNoteEvent.from_content(keys, "Hello World!")

    asyncio.get_event_loop().run_until_complete(
        utils.send_and_expect_command_result(
            signed_event, request_queue, response_queue
        )
    )
    return signed_event


@pytest.fixture
def signed_repost_event(keys, text_note):
    return repost_event.RepostEvent.from_text_note_event(
        keys, text_note, relay_url="ws://nostr.com.se"
    )


@pytest.mark.usefixtures("ctx")
async def test_repost_basic(signed_repost_event, request_queue, response_queue):
    await utils.send_and_expect_command_result(
        signed_repost_event, request_queue, response_queue
    )


@pytest.mark.usefixtures("ctx")
async def test_query_repost_by_repost_author(
    signed_repost_event, keys, request_queue, response_queue
):
    await utils.send_and_expect_command_result(
        signed_repost_event, request_queue, response_queue
    )

    fltr = {"authors": [keys.public], "kinds": [6]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_repost_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_query_repost_by_base_event(
    signed_repost_event, text_note, request_queue, response_queue
):
    await utils.send_and_expect_command_result(
        signed_repost_event, request_queue, response_queue
    )

    fltr = {"#e": [text_note.id]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_repost_event(response_queue)
    await utils.expect_eose(response_queue)


@pytest.mark.usefixtures("ctx")
async def test_query_repost_by_base_event_author(
    signed_repost_event, text_note, request_queue, response_queue
):
    await utils.send_and_expect_command_result(
        signed_repost_event, request_queue, response_queue
    )

    fltr = {"#p": [text_note.pubkey]}

    await utils.send_req_with_filter("1", [fltr], request_queue)
    await utils.expect_repost_event(response_queue)
    await utils.expect_eose(response_queue)
