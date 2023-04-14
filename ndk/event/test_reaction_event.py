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
# https://github.com/nostr-protocol/nips/blob/master/18.md

import pytest

from ndk import crypto, exceptions, types
from ndk.event import event_tags, reaction_event, text_note_event

TEST_AUTHOR = crypto.PublicKeyStr(
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
)
TEST_EVENT_ID = types.EventID(
    "1212121212121212121212121212121212121212121212121212121212121212"
)
TEST_RELAY_URL = "ws://nostr.com.se"
VALID_TAG_1 = ["e", TEST_EVENT_ID, TEST_RELAY_URL]
VALID_TAG_2 = ["p", TEST_AUTHOR]


def test_no_tags(keys):
    with pytest.raises(exceptions.ValidationError):
        reaction_event.ReactionEvent.build(
            keys=keys,
            kind=types.EventKind.REACTION,
        )


def test_two_tags_no_p(keys):
    with pytest.raises(exceptions.ValidationError):
        reaction_event.ReactionEvent.build(
            keys=keys,
            kind=types.EventKind.REACTION,
            tags=event_tags.EventTags([VALID_TAG_1, VALID_TAG_1]),
        )


def test_two_tags_no_e(keys):
    with pytest.raises(exceptions.ValidationError):
        reaction_event.ReactionEvent.build(
            keys=keys,
            kind=types.EventKind.REACTION,
            tags=event_tags.EventTags([VALID_TAG_2, VALID_TAG_2]),
        )


def test_minimum_valid(keys):
    reaction_event.ReactionEvent.build(
        keys=keys,
        kind=types.EventKind.REACTION,
        tags=event_tags.EventTags([VALID_TAG_1, VALID_TAG_2]),
    )


def test_no_tag_text_note(keys):
    event = text_note_event.TextNoteEvent.from_content(
        keys=keys, content="Hello, world!"
    )
    reaction = reaction_event.ReactionEvent.from_text_note_event(
        keys=keys, text_note=event, content="+"
    )

    assert ["e", event.id] in reaction.tags.get("e")
    assert ["p", event.pubkey] in reaction.tags.get("p")
    assert reaction.content == "+"


def test_text_note_with_e_p_tags(keys):
    event = text_note_event.TextNoteEvent.from_content(
        keys=keys,
        content="Hello, world!",
        tags=event_tags.EventTags([VALID_TAG_1, VALID_TAG_2]),
    )

    reaction = reaction_event.ReactionEvent.from_text_note_event(
        keys=keys, text_note=event, content="+"
    )

    assert ["e", event.id] in reaction.tags
    assert VALID_TAG_1 in reaction.tags
    assert ["p", event.pubkey] in reaction.tags
    assert VALID_TAG_2 in reaction.tags
    assert reaction.content == "+"
