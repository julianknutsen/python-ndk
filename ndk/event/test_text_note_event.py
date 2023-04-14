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

from ndk import types
from ndk.event import event_tags, text_note_event

VALID_PUBKEY_STR = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"


def test_from_content_no_tags(keys):
    ev = text_note_event.TextNoteEvent.from_content(keys, "Hello World!")
    assert ev.kind == types.EventKind.TEXT_NOTE
    assert ev.tags == event_tags.EventTags([])
    assert ev.content == "Hello World!"


def test_from_content_with_tags(keys):
    ev = text_note_event.TextNoteEvent.from_content(
        keys, "Hello World!", tags=event_tags.EventTags([["p", VALID_PUBKEY_STR]])
    )
    assert ev.kind == types.EventKind.TEXT_NOTE
    assert ev.tags == event_tags.EventTags([["p", VALID_PUBKEY_STR]])
    assert ev.content == "Hello World!"
