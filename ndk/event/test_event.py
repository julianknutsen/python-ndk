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

from unittest import mock

import pytest

from ndk import crypto, serialize
from ndk.event import event, metadata_event


def test_create_set_metadata_message():
    keys = crypto.KeyPair()
    unsigned_event = metadata_event.MetadataEvent.from_metadata_parts(
        "bob", "#nostr", "http://picture.com"
    )
    signed_event = event.build_signed_event(unsigned_event, keys)
    m = serialize.deserialize(signed_event.serialize())

    assert len(m) == 2
    assert m[0] == "EVENT"

    e = m[1]

    assert len(e["id"]) == 64
    assert e["pubkey"] == keys.public
    assert e["kind"] == event.EventKind.SET_METADATA.value
    assert e["tags"] == [[]]
    assert serialize.deserialize(e["content"]) == {
        "name": "bob",
        "about": "#nostr",
        "picture": "http://picture.com",
    }
    assert len(e["sig"]) == 128


def test_unsigned_event_created_in_future():
    keys = crypto.KeyPair()
    unsigned_event = event.UnsignedEvent(created_at=2)

    with pytest.raises(ValueError, match=".*in the past.*"):
        with mock.patch("time.time", return_value=1):
            event.build_signed_event(unsigned_event, keys)
