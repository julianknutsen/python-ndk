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

from ndk.event import serialize
from ndk.messages import request


def test_init_wrong_type_sub_id():
    with pytest.raises(TypeError):
        request.Request(1, [])  # type: ignore


def test_init_wrong_type_filters():
    with pytest.raises(TypeError):
        request.Request("1", {})  # type: ignore


def test_init_empty_filters():
    with pytest.raises(TypeError):
        request.Request("1", [])


def test_serialize():
    r = request.Request("1", [{}])
    serialized = r.serialize()

    deserialized = serialize.deserialize(serialized)

    assert deserialized == ["REQ", "1", {}]


def test_serialize_multiple_filters():
    r = request.Request("1", [{}, {}])
    serialized = r.serialize()

    deserialized = serialize.deserialize(serialized)

    assert deserialized == ["REQ", "1", {}, {}]
