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

from ndk.event import event


class EventRepo:
    _stored_events: list[event.SignedEvent]

    def __init__(self):
        self._stored_events = []

    def add(self, ev: event.SignedEvent) -> event.EventID:
        self._stored_events.append(ev)
        return ev.id

    def get(self, fltrs: list[dict]) -> list[event.SignedEvent]:
        fetched: list[event.SignedEvent] = []

        for fltr in fltrs:
            tmp = [
                event
                for event in self._stored_events
                if ("ids" not in fltr or event.id in fltr["ids"])
                and ("authors" not in fltr or event.pubkey in fltr["authors"])
                and ("kinds" not in fltr or event.kind in fltr["kinds"])
                and ("since" not in fltr or event.created_at > fltr["since"])
                and ("until" not in fltr or event.created_at < fltr["until"])
            ]

            if "limit" in fltr:
                tmp = tmp[-fltr["limit"] :]

            fetched.extend(tmp)

        return fetched
