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

import dataclasses

from ndk import exceptions, serialize
from ndk.event import event
from ndk.messages import message


@dataclasses.dataclass
class Event(message.WriteableMessage, message.ReadableMessage):
    event_dict: dict

    @classmethod
    def from_signed_event(cls, signed_event: event.SignedEvent):
        return cls(signed_event.__dict__)

    def serialize(self) -> str:
        return serialize.serialize_as_str(["EVENT", self.event_dict])

    @classmethod
    def deserialize_list(cls, lst: list):
        assert len(lst) > 0
        assert lst[0] == "EVENT"

        if len(lst) != 2:
            raise exceptions.ParseError(
                f"Unexpected format of Event message. Expected two items, but got: {lst}"
            )

        return cls(*lst[1:])
