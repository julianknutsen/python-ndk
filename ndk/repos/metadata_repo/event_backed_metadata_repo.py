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

import logging
import typing

from ndk import crypto
from ndk.event import (
    contact_list_event,
    event,
    metadata_event,
    recommend_server_event,
    serialize,
)
from ndk.repos import contacts
from ndk.repos.event_repo import event_repo
from ndk.repos.metadata_repo import metadata_repo


class EventBackedMetadataRepo(metadata_repo.MetadataRepo):
    _event_repo: event_repo.EventRepo

    def __init__(self, ev_repo: event_repo.EventRepo):
        self._event_repo = ev_repo

    def overwrite(
        self,
        keys: crypto.KeyPair,
        name: typing.Optional[str] = None,
        about: typing.Optional[str] = None,
        picture: typing.Optional[str] = None,
        recommend_server: str = "",
        contact_list: typing.Optional[contacts.ContactList] = None,
    ) -> bool:
        mev = metadata_event.MetadataEvent.from_metadata_parts(name, about, picture)
        rsev = recommend_server_event.RecommendServerEvent.from_url(recommend_server)
        clev = contact_list_event.ContactListEvent.from_contact_list(contact_list)

        return all(
            self._event_repo.add(event.build_signed_event(ev, keys))
            for ev in [mev, rsev, clev]
        )

    def get(self, pubkey: crypto.PublicKeyStr) -> dict[str, object]:
        metadata = {}
        mev = self._event_repo.get_latest_by_author(
            event.EventKind.SET_METADATA, pubkey
        )
        if mev:
            metadata = serialize.deserialize(mev.content)
        else:
            logging.debug("No MetadataEvent returned")

        rsev = self._event_repo.get_latest_by_author(
            event.EventKind.RECOMMEND_SERVER, pubkey
        )
        if rsev:
            metadata["recommend_server"] = rsev.content
        else:
            metadata["recommend_server"] = ""
            logging.debug("No RecommendServerEvent returned")

        clev = self._event_repo.get_latest_by_author(
            event.EventKind.CONTACT_LIST, pubkey
        )
        if clev:
            metadata["contacts"] = clev.get_contact_list()  # type: ignore
        else:
            metadata["contacts"] = contacts.ContactList()
            logging.debug("No ContactListEvent returned")

        return metadata
