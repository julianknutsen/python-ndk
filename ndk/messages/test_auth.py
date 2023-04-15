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
from ndk.messages import auth


def test_init_wrong_type():
    with pytest.raises(TypeError):
        auth.Auth(1)  # type: ignore


def test_close_message_empty():
    msg = ["AUTH"]

    with pytest.raises(TypeError):
        auth.Auth.deserialize_list(msg)


def test_close_correct():
    msg = ["AUTH", "challenge"]

    c = auth.Auth.deserialize_list(msg)

    assert c.challenge == "challenge"


def test_serialize():
    c = auth.Auth("1")
    serialized = c.serialize()

    deserialized = serialize.deserialize(serialized)

    assert deserialized == ["AUTH", "1"]
