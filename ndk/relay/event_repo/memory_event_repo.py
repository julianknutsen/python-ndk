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

import collections

from ndk import types
from ndk.event import event, event_filter
from ndk.relay.event_repo import event_repo


class MemoryEventRepo(event_repo.EventRepo):
    _stored_events: dict[types.EventID, event.Event]

    def __init__(self):
        self._stored_events = {}
        super().__init__()

    async def _persist(self, ev: event.Event) -> types.EventID:
        self._stored_events[ev.id] = ev
        return ev.id

    async def get(self, fltrs: list[event_filter.EventFilter]) -> list[event.Event]:
        fetched: collections.OrderedDict[
            types.EventID, event.Event
        ] = collections.OrderedDict()

        for fltr in fltrs:
            tmp = [
                event
                for event in self._stored_events.values()
                if fltr.matches_event(event)
            ]

            if fltr.limit is not None:
                tmp = tmp[-fltr.limit :]

            for ev in tmp:
                if ev.id not in fetched:
                    fetched[ev.id] = ev

        return sorted(fetched.values(), key=lambda ev: ev.created_at, reverse=True)

    async def remove(self, event_id: types.EventID):
        if event_id not in self._stored_events:
            raise ValueError(f"Event {event_id} not found")
        del self._stored_events[event_id]
