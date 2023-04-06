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

"""Implementation of an EventRepo that is backed by a single Relay.

Typical usage example::
    keys = crypto.KeyPair()
    repo = RelayEventRepo(XXX)
    event_id = repo.add(keys, <UnsignedEvent>)
    event = repo.get(event_id)
"""

import logging
import typing

from ndk import crypto, types
from ndk.event import event, event_filter
from ndk.repos.event_repo import event_repo, protocol_handler

SendFn = typing.Callable[[str], int]
RecvFn = typing.Callable[[], str]
SubID = typing.NewType("SubID", str)


class RelayEventRepo(event_repo.EventRepo):
    """Concrete implementation of EventRepo that delegates to a single Relay.
    This class handles the nostr protocol messages between the client
    and server to add new events and get existing events.
    """

    _protocol: protocol_handler.ProtocolHandler

    def __init__(self, protocol: protocol_handler.ProtocolHandler):
        self._protocol = protocol
        super().__init__()

    async def add(self, signed_ev: event.SignedEvent) -> types.EventID:
        result = await self._protocol.write_event(signed_ev)

        if not result.accepted:
            logging.debug("Failed adding event to relay: %s", result.message)
            raise event_repo.AddItemError(
                f"Failed to add {signed_ev}: {result.message}"
            )

        if "duplicate" in result.message:
            logging.debug("Duplicate event sent to relay: %s", result.message)

        return types.EventID(result.event_id)

    async def get(self, ev_id: types.EventID) -> event.UnsignedEvent:
        events = await self._protocol.query_events(
            [event_filter.EventFilter(ids=[ev_id])]
        )

        if not events:
            raise event_repo.GetItemError("No event returned from query for {ev_id}")

        if len(events) > 1:
            raise event_repo.GetItemError(
                f"Expected a single stored event, but received: {events}"
            )

        return events[0]

    async def get_by_author(
        self,
        kind: event.EventKind,
        author: crypto.PublicKeyStr,
        limit: int = 0,
    ) -> typing.Sequence[event.UnsignedEvent]:
        fltr = event_filter.EventFilter(kinds=[kind], authors=[author])

        if limit:
            fltr.limit = limit

        return await self._protocol.query_events([fltr])
