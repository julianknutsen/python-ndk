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

from ndk.event import event, event_filter
from relay import event_handler


class EventRepo(abc.ABC):
    _insert_event_handler: event_handler.EventHandler

    def __init__(self) -> None:
        self._insert_event_handler = event_handler.EventHandler()
        super().__init__()

    @abc.abstractmethod
    async def add(self, ev: event.SignedEvent) -> event.EventID:
        pass

    @abc.abstractmethod
    async def get(
        self, fltrs: list[event_filter.EventFilter]
    ) -> list[event.SignedEvent]:
        pass

    def register_insert_cb(
        self, cb: event_handler.EventHandlerCb
    ) -> event_handler.EventHandlerCbId:
        return self._insert_event_handler.register(cb)

    def unregister_insert_cb(self, cb_id: event_handler.EventHandlerCbId):
        self._insert_event_handler.unregister(cb_id)
