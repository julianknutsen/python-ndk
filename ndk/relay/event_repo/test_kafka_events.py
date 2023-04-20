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

from ndk.event import metadata_event
from ndk.relay.event_repo import kafka_events


def test_deserialize_no_kind():
    with pytest.raises(ValueError, match="Error deserializing kafka event"):
        kafka_events.KafkaEvent.deserialize(b"{}")


def test_deserialize_unknown_kind():
    with pytest.raises(ValueError, match="Unknown kafka event kind"):
        kafka_events.KafkaEvent.deserialize(b'{"kind": -2}')


def test_serialize_deserialize(keys):
    ev = metadata_event.MetadataEvent.from_metadata_parts(keys)
    kev = kafka_events.CreatOrUpdateEvent.create(ev)

    assert ev == kafka_events.KafkaEvent.deserialize(kev.serialize()).ev
