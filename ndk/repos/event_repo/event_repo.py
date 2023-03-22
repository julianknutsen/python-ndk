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
import typing

from ndk import crypto
from ndk.event import event


class AddItemError(Exception):
    pass


class GetItemError(Exception):
    pass


class EventRepo(abc.ABC):
    @abc.abstractmethod
    async def add(self, signed_ev: event.SignedEvent) -> event.EventID:
        """Adds the SignedEvent to the repo

        Args:
            signed_ev (event.SignedEvent): The event to add

        Returns:
            event.EventID: An id that can be used to get the SignedEvent later
        """

    @abc.abstractmethod
    async def get(self, ev_id: event.EventID):
        """Retrieves a previously added SignedEvent by id

        Args:
            ev_id (event.EventID): The id of the event to retrieve
        """

    @abc.abstractmethod
    async def get_by_author(
        self,
        kind: event.EventKind,
        author: crypto.PublicKeyStr,
        limit: int = 0,
    ) -> typing.Sequence[event.UnsignedEvent]:
        """Retrieve Events of a given kind.

        Args:
            kind (event.EventKind): The kind to match
            author (crypto.PublicKeyStr): The pubkey of the author of the event to match
            limit (int, optional): The maximum number of events to return. May return fewer. Defaults to 0.

        Returns:
            typing.Sequence[event.UnsignedEvent]: Specific subclass of UnsignedEvent are returned. e.g. MetadataEvent for kind == 0
        """

    async def get_latest_by_author(
        self, kind: event.EventKind, author: crypto.PublicKeyStr
    ) -> typing.Optional[event.UnsignedEvent]:
        """Convenience function to return the latest single event of a given kind from a specific author

        Args:
            kind (event.EventKind): The kind to match
            author (crypto.PublicKeyStr): The pubkey of the author of the event to match

        Raises:
            GetItemError: Raises if any error was encountered during the retrieval

        Returns:
            typing.Optional[event.UnsignedEvent]: Returns a subclass of UnsignedEvent based on kind. Return None if no event was found.
        """
        events = list(
            await self.get_by_author(
                kind,
                author,
                1,
            )
        )

        if not events:
            return None

        return events[0]
