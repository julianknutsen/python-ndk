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
# pylint: disable=redefined-outer-name, unused-argument, protected-access

import pytest

from ndk import serialize
from ndk.event import auth_event
from ndk.relay import auth_handler

VALID_RELAY_URL = "wss://relay.example.com"


def test_default_is_authenticated():
    h = auth_handler.AuthHandler(VALID_RELAY_URL)
    assert not h.is_authenticated()


def test_build_auth_message():
    h = auth_handler.AuthHandler(VALID_RELAY_URL)
    m = serialize.deserialize(h.build_auth_message())
    assert m[0] == "AUTH"
    assert isinstance(m[1], str)


def test_handle_auth_event_wrong_relay(keys):
    h = auth_handler.AuthHandler(VALID_RELAY_URL)
    with pytest.raises(ValueError, match="expected relay"):
        h.handle_auth_event(
            auth_event.AuthEvent.from_parts(keys, "wss://wrong.example.com", "1")
        )
    assert not h.is_authenticated()


def test_handle_auth_event_wrong_challenge(keys):
    h = auth_handler.AuthHandler(VALID_RELAY_URL)
    with pytest.raises(ValueError, match="expected challenge"):
        h.handle_auth_event(auth_event.AuthEvent.from_parts(keys, VALID_RELAY_URL, "1"))
    assert not h.is_authenticated()


def test_handle_auth_event(keys):
    h = auth_handler.AuthHandler(VALID_RELAY_URL)
    h.handle_auth_event(
        auth_event.AuthEvent.from_parts(keys, VALID_RELAY_URL, h._challenge)
    )
    assert h.is_authenticated()
