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
import uuid

from ndk.event import event

EventNotifierCbId = typing.NewType("EventNotifierCbId", str)
EventNotifierCb = typing.Callable[[event.SignedEvent], typing.Awaitable]


class EventNotifier:
    _cbs: dict[EventNotifierCbId, EventNotifierCb]

    def __init__(self):
        self._cbs = {}

    def register(self, cb: EventNotifierCb) -> EventNotifierCbId:
        cb_id = EventNotifierCbId(str(uuid.uuid4()))
        self._cbs[cb_id] = cb
        return cb_id

    def unregister(self, cb_id: EventNotifierCbId):
        if cb_id not in self._cbs:
            raise ValueError(f"Unknown callback id {cb_id}")
        del self._cbs[cb_id]

    async def handle_event(self, ev: event.SignedEvent):
        for cb in self._cbs.values():
            await cb(ev)
