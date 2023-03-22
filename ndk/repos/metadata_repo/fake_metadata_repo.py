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

import typing

from ndk import crypto
from ndk.repos import contacts
from ndk.repos.metadata_repo import metadata_repo


class FakeMetadataRepository(metadata_repo.MetadataRepo):
    _metadata: dict[crypto.PublicKeyStr, dict[str, object]]

    def __init__(self):
        self._metadata = {}

    async def overwrite(
        self,
        keys: crypto.KeyPair,
        name: typing.Optional[str] = None,
        about: typing.Optional[str] = None,
        picture: typing.Optional[str] = None,
        recommend_server: str = "",
        contact_list: typing.Optional[contacts.ContactList] = None,
    ) -> bool:
        metadata = metadata_repo.DEFAULT_METADATA

        if name:
            metadata["name"] = name

        if about:
            metadata["about"] = about

        if picture:
            metadata["picture"] = picture

        if recommend_server:
            metadata["recommend_server"] = recommend_server

        if contact_list:
            metadata["contacts"] = contact_list

        self._metadata[keys.public] = metadata
        return True

    async def get(self, pubkey: crypto.PublicKeyStr) -> dict[str, object]:
        if pubkey not in self._metadata:
            return metadata_repo.DEFAULT_METADATA

        return self._metadata[pubkey]
