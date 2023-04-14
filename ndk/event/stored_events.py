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

import typing

from ndk.event import event, event_builder
from ndk.messages import eose, message, notice, relay_event


class StoredEvents:
    _events: list[event.SignedEvent]
    _complete: bool = False

    def __init__(self):
        self._events = []

    def get(self) -> typing.Sequence[event.SignedEvent]:
        assert self._complete, "cant access results before processing complete"
        return self._events

    def process_msg(self, msg: message.Message) -> bool:
        assert not self._complete, "should not call process_token after complete"

        if isinstance(msg, eose.EndOfStoredEvents):
            self._complete = True
            return True

        if isinstance(msg, notice.Notice):
            raise RuntimeError(f"NOTICE response from server: {msg.message}")

        if not isinstance(msg, relay_event.RelayEvent):
            raise RuntimeError(f"Unhandled message type: {msg}")

        self._events.append(event_builder.from_dict(msg.event_dict))
        return False
