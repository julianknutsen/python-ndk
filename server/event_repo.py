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

    def add(self, ev: event.SignedEvent):
        self._stored_events.append(ev)

    def get(self, fltrs: list[dict]) -> list[event.SignedEvent]:
        fetched: list[event.SignedEvent] = []

        for fltr in fltrs:
            # only id fetch
            if set(["ids"]) == set(fltr.keys()):
                for ev_id in fltr["ids"]:
                    for ev in self._stored_events:
                        if ev.id == ev_id:
                            fetched.append(ev)

            # search by kind & author
            elif set(["kinds", "authors", "limit"]) == set(fltr.keys()) or set(
                ["kinds", "authors"]
            ) == set(fltr.keys()):
                limit = 0
                if "limit" in fltr:
                    limit = fltr["limit"]

                fetched = sorted(
                    [
                        ev
                        for ev in self._stored_events
                        if ev.kind in fltr["kinds"] and ev.pubkey in fltr["authors"]
                    ],
                    key=lambda ev: ev.created_at,
                )[-limit:]

        return fetched
