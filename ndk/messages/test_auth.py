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

from ndk import serialize
from ndk.event import auth_event, metadata_event
from ndk.messages import auth


def test_init_wrong_type():
    with pytest.raises(TypeError):
        auth.AuthRequest(1)  # type: ignore


def test_auth_message_empty():
    msg = ["AUTH"]

    with pytest.raises(TypeError):
        auth.Auth.deserialize_list(msg)


def test_auth_message_wrong_type():
    msg = ["AUTH", 1]

    with pytest.raises(TypeError):
        auth.Auth.deserialize_list(msg)


def test_auth_request_message_empty():
    msg = ["AUTH"]

    with pytest.raises(TypeError):
        auth.AuthRequest.deserialize_list(msg)


def test_auth_request_correct():
    msg = ["AUTH", "challenge"]

    c = auth.AuthRequest.deserialize_list(msg)

    assert c.challenge == "challenge"


def test_auth_request_serialize():
    c = auth.AuthRequest("1")
    serialized = c.serialize()

    deserialized = serialize.deserialize(serialized)

    assert deserialized == ["AUTH", "1"]


def test_auth_response_init_wrong_type():
    with pytest.raises(TypeError):
        auth.AuthResponse(1)  # type: ignore


def test_auth_response_message_empty():
    msg = ["AUTH"]

    with pytest.raises(TypeError):
        auth.AuthResponse.deserialize_list(msg)


def test_auth_response_correct(keys):
    ev = auth_event.AuthEvent.from_parts(keys, "wss://localhost", "1234")
    msg = ["AUTH", ev.__dict__]

    c = auth.AuthResponse.deserialize_list(msg)

    assert c.ev == ev


def test_auth_response_deserialize_list(keys):
    ev = auth_event.AuthEvent.from_parts(keys, "wss://localhost", "1234")
    c = auth.AuthResponse(ev)

    auth.AuthResponse.deserialize_list(serialize.deserialize(c.serialize()))


def test_auth_response_deserialize_bad_payload(keys):
    wrong_ev = metadata_event.MetadataEvent.from_metadata_parts(keys)
    msg = ["AUTH", wrong_ev.__dict__]
    with pytest.raises(ValueError, match="Unexpected format of AUTH message"):
        auth.AuthResponse.deserialize_list(
            serialize.deserialize(serialize.serialize_as_str(msg))
        )
