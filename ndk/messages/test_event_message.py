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

import pytest

from ndk import crypto, exceptions, serialize
from ndk.event import event, metadata_event
from ndk.messages import event_message


def test_init_wrong_type():
    with pytest.raises(TypeError):
        event_message.Event(1)  # type: ignore


def test_serialize():
    r = event_message.Event({})
    serialized = r.serialize()

    deserialized = serialize.deserialize(serialized)

    assert deserialized == ["EVENT", {}]


def test_from_signed_event():
    keys = crypto.KeyPair()
    unsigned_event = metadata_event.MetadataEvent.from_metadata_parts(
        "bob", "#nostr", "http://picture.com"
    )
    signed_event = event.build_signed_event(unsigned_event, keys)
    _, body = serialize.deserialize(
        event_message.Event.from_signed_event(signed_event).serialize()
    )

    assert len(body["id"]) == 64
    assert body["pubkey"] == keys.public
    assert body["kind"] == event.EventKind.SET_METADATA.value
    assert body["tags"] == []
    assert serialize.deserialize(body["content"]) == {
        "name": "bob",
        "about": "#nostr",
        "picture": "http://picture.com",
    }
    assert len(body["sig"]) == 128


def test_deserialize_list_bad_length():
    with pytest.raises(exceptions.ParseError):
        event_message.Event.deserialize_list(["EVENT"])


def test_deserialize_list():
    keys = crypto.KeyPair()
    unsigned_event = metadata_event.MetadataEvent.from_metadata_parts()
    signed_event = event.build_signed_event(unsigned_event, keys)
    event_msg = event_message.Event.from_signed_event(signed_event)
    lst = serialize.deserialize(event_msg.serialize())
    ev = event_message.Event.deserialize_list(lst)

    assert ev == event_msg
