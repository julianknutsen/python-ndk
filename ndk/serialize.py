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

"""Serialization utility for Nostr object.

In general, no code should call encode() or use the builtin json library explicitly
in favor of delegating to this utility module to handle the sharp edges.

Example::

    nostr_obj: Event

    back_and_forth = deserialize(serialize_as_str(nostr_obj))
    assert nostr_obj == back_and_forth
"""

import json
import typing


def serialize_as_str(obj) -> str:
    """Serialize any python object for the wire based on nostr specs

    Args:
        obj (typing.Any): any object, but typically a list or dict

    Returns:
        str: encoded string representation of obj
    """

    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def serialize_as_bytes(obj) -> bytes:
    """Serialize any Python object as bytes

    Useful for hashing

    Args:
        obj (typing.Any): any object, but typically a list or dict

    Returns:
        bytes: serialized object as raw bytes encoded as utf-8
    """
    return serialize_as_str(obj).encode("utf-8")


def deserialize(serialized_obj: str) -> typing.Any:
    """Deserialize a str into a Python object according to Nostr spec

    Args:
        s (str): serialized object

    Returns:
        typing.Any: Python object
    """
    return json.loads(serialized_obj)
