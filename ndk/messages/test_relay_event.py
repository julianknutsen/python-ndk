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

import pytest

from ndk.event import serialize
from ndk.messages import message_factory, relay_event


def test_input_non_list():
    msg = {}

    with pytest.raises(AssertionError):
        relay_event.RelayEvent.deserialize(msg)  # type: ignore


def test_bad_len():
    msg = ["EVENT"]

    with pytest.raises(TypeError):
        relay_event.RelayEvent.deserialize(msg)


def test_wrong_type_sub_id():
    msg = ["EVENT", 1, {}]

    with pytest.raises(TypeError):
        relay_event.RelayEvent.deserialize(msg)


def test_wrong_type_event():
    msg = ["EVENT", "subscription-id", []]

    with pytest.raises(TypeError):
        relay_event.RelayEvent.deserialize(msg)


def test_correct():
    msg = ["EVENT", "subscription-id", {}]

    n = relay_event.RelayEvent.deserialize(msg)

    assert n.sub_id == "subscription-id"


def test_factory():
    msg = ["EVENT", "subscription-id", {}]

    n = message_factory.from_str(serialize.serialize_as_str(msg))

    assert isinstance(n, relay_event.RelayEvent)
