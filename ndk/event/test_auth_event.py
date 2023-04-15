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

import time

import mock
import pytest

from ndk import types
from ndk.event import auth_event, event_builder, event_tags

VALID_RELAY_URL = "wss://nostr.com.se"
VALID_TAGS = event_tags.EventTags([["relay", VALID_RELAY_URL], ["challenge", "foobar"]])


def test_from_parts(keys):
    ev = auth_event.AuthEvent.from_parts(keys, VALID_RELAY_URL, "foobar")
    assert ev.kind == types.EventKind.AUTH
    assert ev.tags == VALID_TAGS
    assert ev.content == ""


def test_init_bad_kind(keys):
    with pytest.raises(ValueError):
        auth_event.AuthEvent.build(keys, types.EventKind.REACTION, tags=VALID_TAGS)


def test_init_too_old(keys):
    now = int(time.time())
    with mock.patch("time.time", return_value=now):
        with pytest.raises(ValueError):
            auth_event.AuthEvent.build(
                keys, types.EventKind.AUTH, created_at=now + 601, tags=VALID_TAGS
            )


def test_init_too_new(keys):
    now = int(time.time())
    with mock.patch("time.time", return_value=now):
        with pytest.raises(ValueError):
            auth_event.AuthEvent.build(
                keys, types.EventKind.AUTH, created_at=now - 601, tags=VALID_TAGS
            )


def test_init_bad_tags(keys):
    with pytest.raises(ValueError):
        auth_event.AuthEvent.build(
            keys,
            types.EventKind.AUTH,
            tags=event_tags.EventTags([["relay", VALID_RELAY_URL]]),
        )


def test_init_bad_tags2(keys):
    with pytest.raises(ValueError):
        auth_event.AuthEvent.build(
            keys,
            types.EventKind.AUTH,
            tags=event_tags.EventTags([["challenge", "foobar"]]),
        )


def test_event_builder(keys):
    ev = auth_event.AuthEvent.from_parts(keys, VALID_RELAY_URL, "foobar")

    ev2 = event_builder.from_dict(ev.__dict__)

    assert ev == ev2
