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

from ndk import crypto, types
from ndk.event import event


class AddItemError(Exception):
    pass


class GetItemError(Exception):
    pass


class EventRepo(abc.ABC):
    @abc.abstractmethod
    async def add(self, ev: event.Event) -> types.EventID:
        """Adds the Event to the repo

        Args:
            ev (event.Event): The event to add

        Returns:
            types.EventID: An id that can be used to get the Event later
        """

    @abc.abstractmethod
    async def get(self, ev_id: types.EventID):
        """Retrieves a previously added Event by id

        Args:
            ev_id (types.EventID): The id of the event to retrieve
        """

    @abc.abstractmethod
    async def get_by_author(
        self,
        kind: types.EventKind,
        author: crypto.PublicKeyStr,
        limit: int = 0,
    ) -> typing.Sequence[event.Event]:
        """Retrieve Events of a given kind.

        Args:
            kind (types.EventKind): The kind to match
            author (crypto.PublicKeyStr): The pubkey of the author of the event to match
            limit (int, optional): The maximum number of events to return. May return fewer. Defaults to 0.

        Returns:
            typing.Sequence[event.Event]: Specific subclass of Event are returned. e.g. MetadataEvent for kind == 0
        """

    async def get_latest_by_author(
        self, kind: types.EventKind, author: crypto.PublicKeyStr
    ) -> typing.Optional[event.Event]:
        """Convenience function to return the latest single event of a given kind from a specific author

        Args:
            kind (types.EventKind): The kind to match
            author (crypto.PublicKeyStr): The pubkey of the author of the event to match

        Raises:
            GetItemError: Raises if any error was encountered during the retrieval

        Returns:
            typing.Optional[event.Event]: Returns a subclass of Event based on kind. Return None if no event was found.
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
