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

import abc
import dataclasses

from ndk import serialize
from ndk.event import event, event_builder


class KafkaEventKind:
    INVALID = -1
    CREATE = 1


@dataclasses.dataclass
class KafkaEvent(abc.ABC):
    kind: int

    def serialize(self) -> bytes:
        return serialize.serialize_as_bytes(self.to_dict())

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass

    @staticmethod
    def deserialize(data: bytes):
        d = serialize.deserialize_bytes(data)
        if "kind" not in d:
            raise ValueError("Error deserializing kafka event")

        kind = d["kind"]
        if kind == KafkaEventKind.CREATE:
            return CreatOrUpdateEvent.from_dict(d)
        else:
            raise ValueError("Unknown kafka event kind")


@dataclasses.dataclass
class CreatOrUpdateEvent(KafkaEvent):
    ev: event.Event

    @classmethod
    def create(cls, ev: event.Event):
        return cls(KafkaEventKind.CREATE, ev)

    def to_dict(self) -> dict:
        d = self.__dict__
        d["ev"] = self.ev.__dict__
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls.create(event_builder.from_validated_dict(d["ev"]))
