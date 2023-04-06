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

"""Implementation of an EventRepo that is backed by memory.

Typical usage example::
    keys = crypto.KeyPair()
    repo = MemoryEventRepo()
    event_id = repo.add(keys, <UnsignedEvent>)
    event = repo.get(event_id)
"""

import typing

from ndk import crypto, types
from ndk.event import event, event_parser
from ndk.repos.event_repo import event_repo


class MemoryEventRepo(event_repo.EventRepo):
    """Concrete implementation of EventRepo that is backed by memory."""

    _by_id: dict[types.EventID, event.SignedEvent]

    def __init__(self):
        self._by_id = {}
        super().__init__()

    async def add(self, signed_ev: event.SignedEvent) -> types.EventID:
        self._by_id[signed_ev.id] = signed_ev
        return signed_ev.id

    async def get(self, ev_id: types.EventID):
        if ev_id not in self._by_id:
            raise event_repo.GetItemError("Unknown ev_id")

        return self._by_id[ev_id]

    async def get_by_author(
        self,
        kind: event.EventKind,
        author: crypto.PublicKeyStr,
        limit: int = 0,
    ) -> typing.Sequence[event.UnsignedEvent]:
        if limit <= 0:
            limit = len(self._by_id)

        return sorted(
            [
                event_parser.signed_to_unsigned(ev)
                for ev in self._by_id.values()
                if ev.kind == kind and ev.pubkey == author
            ],
            key=lambda ev: ev.created_at,
        )[-limit:]
