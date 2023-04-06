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
# https://github.com/nostr-protocol/nips/blob/master/18.md

import pytest

from ndk import crypto, exceptions, types
from ndk.event import event, event_tags, repost_event

TEST_AUTHOR = crypto.PublicKeyStr(
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
)
TEST_EVENT_ID = types.EventID(
    "1212121212121212121212121212121212121212121212121212121212121212"
)
TEST_RELAY_URL_SSL = "wss://nostr.com.se"
TEST_RELAY_URL = "ws://nostr.com.se"
VALID_TAG_1 = ["e", TEST_EVENT_ID, TEST_RELAY_URL]
VALID_TAG_2 = ["p", TEST_AUTHOR]


def test_basic():
    ev = repost_event.RepostEvent.from_parts(TEST_EVENT_ID, TEST_AUTHOR, TEST_RELAY_URL)
    assert ev.content == ""


def test_ssl_relay():
    repost_event.RepostEvent.from_parts(TEST_EVENT_ID, TEST_AUTHOR, TEST_RELAY_URL_SSL)


def test_no_tags():
    with pytest.raises(exceptions.ValidationError):
        repost_event.RepostEvent(
            kind=event.EventKind.REPOST, tags=event_tags.EventTags([]), content=""
        )


def test_one_tag_wrong_type():
    with pytest.raises(exceptions.ValidationError):
        repost_event.RepostEvent(
            kind=event.EventKind.REPOST,
            tags=event_tags.EventTags([["a", "foo"]]),
            content="",
        )


def test_two_tag_wrong_second_type():
    with pytest.raises(exceptions.ValidationError):
        repost_event.RepostEvent(
            kind=event.EventKind.REPOST,
            tags=event_tags.EventTags([VALID_TAG_1, ["a", "foo"]]),
            content="",
        )


def test_two_tag_order_1():
    repost_event.RepostEvent(
        kind=event.EventKind.REPOST,
        tags=event_tags.EventTags([VALID_TAG_1, VALID_TAG_2]),
        content="",
    )


def test_two_tag_order_2():
    repost_event.RepostEvent(
        kind=event.EventKind.REPOST,
        tags=event_tags.EventTags([VALID_TAG_2, VALID_TAG_1]),
        content="",
    )
