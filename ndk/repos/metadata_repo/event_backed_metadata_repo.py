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

import asyncio
import logging
import typing

from ndk import crypto, serialize, types
from ndk.event import contact_list_event, metadata_event, recommend_server_event
from ndk.repos import contacts
from ndk.repos.event_repo import event_repo
from ndk.repos.metadata_repo import metadata_repo

logger = logging.getLogger(__name__)


class EventBackedMetadataRepo(metadata_repo.MetadataRepo):
    _event_repo: event_repo.EventRepo

    def __init__(self, ev_repo: event_repo.EventRepo):
        self._event_repo = ev_repo

    async def overwrite(
        self,
        keys: crypto.KeyPair,
        name: typing.Optional[str] = None,
        about: typing.Optional[str] = None,
        picture: typing.Optional[str] = None,
        recommend_server: str = "",
        contact_list: typing.Optional[contacts.ContactList] = None,
    ) -> bool:
        mev = metadata_event.MetadataEvent.from_metadata_parts(
            keys, name, about, picture
        )
        rsev = recommend_server_event.RecommendServerEvent.from_url(
            keys, recommend_server
        )
        clev = contact_list_event.ContactListEvent.from_contact_list(keys, contact_list)

        tasks = []
        for ev in [mev, rsev, clev]:
            tasks.append(asyncio.create_task(self._event_repo.add(ev)))

        await asyncio.gather(*tasks)

        return True

    async def get(self, pubkey: crypto.PublicKeyStr) -> dict[str, object]:
        metadata = {}
        mev = await self._event_repo.get_latest_by_author(
            types.EventKind.SET_METADATA, pubkey
        )
        if mev:
            metadata = serialize.deserialize_str(mev.content)
        else:
            logger.debug("No MetadataEvent returned")

        rsev = await self._event_repo.get_latest_by_author(
            types.EventKind.RECOMMEND_SERVER, pubkey
        )
        if rsev:
            metadata["recommend_server"] = rsev.content
        else:
            metadata["recommend_server"] = ""
            logger.debug("No RecommendServerEvent returned")

        clev = await self._event_repo.get_latest_by_author(
            types.EventKind.CONTACT_LIST, pubkey
        )
        if clev:
            metadata["contacts"] = clev.get_contact_list()  # type: ignore
        else:
            metadata["contacts"] = contacts.ContactList()
            logger.debug("No ContactListEvent returned")

        return metadata
