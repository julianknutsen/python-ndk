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

from ndk import types
from ndk.event import event, event_filter
from ndk.event import parameterized_replaceable_event as pre


class EventRepo(abc.ABC):
    async def add(self, ev: event.Event) -> types.EventID:
        ev_id = await self._persist(ev)

        if isinstance(ev, event.ReplaceableEvent):
            if not isinstance(ev, pre.ParameterizedReplaceableEvent):
                existing_evs = await self.get(
                    [event_filter.EventFilter(authors=[ev.pubkey], kinds=[ev.kind])]
                )
            else:
                fltrs = []
                existing_evs = []
                normalized_d_tag = ev.get_normalized_d_tag_value()
                if normalized_d_tag is None:
                    # search for ["d", ""], or no tag at all, per NIP-33
                    fltrs.append(
                        event_filter.EventFilter(authors=[ev.pubkey], kinds=[ev.kind])
                    )

                    # query language has no way to search for "no tag" so need to check them all
                    existing_evs = await self.get(fltrs)
                    existing_evs = [
                        ev
                        for ev in existing_evs
                        if len(ev.tags) == 0
                        or (ev.tags[0][0] == "d" and ev.tags[0][1] == "")
                    ]
                else:
                    fltrs.append(
                        event_filter.EventFilter(
                            authors=[ev.pubkey],
                            kinds=[ev.kind],
                            generic_tags={"d": [normalized_d_tag]},
                        )
                    )

                    existing_evs = await self.get(fltrs)

            for e in existing_evs[1:]:  # first entry (latest) is the one we just added
                await self.remove(e.id)

        return ev_id

    @abc.abstractmethod
    async def _persist(self, ev: event.Event) -> types.EventID:
        pass

    @abc.abstractmethod
    async def get(self, fltrs: list[event_filter.EventFilter]) -> list[event.Event]:
        pass

    @abc.abstractmethod
    async def remove(self, event_id: types.EventID):
        pass
