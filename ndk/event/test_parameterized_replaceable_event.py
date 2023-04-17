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

from ndk import types
from ndk.event import event_tags
from ndk.event import parameterized_replaceable_event as pre


def test_init_bad_kind(keys):
    with pytest.raises(
        ValueError, match="ParameterizedReplaceableEvent must be in range"
    ):
        pre.ParameterizedReplaceableEvent.build(keys, types.EventKind.REACTION)


def test_normalized_d_tag_no_tags(keys):
    ev = pre.ParameterizedReplaceableEvent.build(keys, kind=30000)
    assert ev.get_normalized_d_tag_value() is None


def test_normalized_d_tag_multiple_d_tags(keys):
    ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, tags=event_tags.EventTags([["d", "foo"], ["d", "bar"]])
    )
    assert ev.get_normalized_d_tag_value() == "foo"


def test_normalized_d_tag_long_d_tag(keys):
    ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, tags=event_tags.EventTags([["d", "foo", "bar"]])
    )
    assert ev.get_normalized_d_tag_value() == "foo"
