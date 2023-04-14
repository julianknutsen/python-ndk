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

from ndk import types
from ndk.event import event, event_filter
from ndk.relay.event_repo import event_repo


class EventHandler:
    _repo: event_repo.EventRepo

    def __init__(self, repo: event_repo.EventRepo):
        self._repo = repo

    async def handle_event(self, ev: event.SignedEvent):
        await self._repo.add(ev)

        if ev.kind in [types.EventKind.SET_METADATA, types.EventKind.CONTACT_LIST]:
            existing_evs = await self._repo.get(
                [event_filter.EventFilter(authors=[ev.pubkey], kinds=[ev.kind])]
            )
            for e in existing_evs[1:]:  # first entry (latest) is the one we just added
                await self._repo.remove(e.id)
