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

"""Convenience wrappers for contact information retrieved from
ContactList (NIP-02) events
"""

import dataclasses
import typing

from ndk import crypto


@dataclasses.dataclass
class ContactInfo:
    pubkey: crypto.PublicKeyStr
    relay_url: str = ""
    petname: str = ""

    def to_event_tag(self) -> list[str]:
        tag = ["p", self.pubkey]

        if self.relay_url:
            tag.append(self.relay_url)

        if self.petname:
            tag.append(self.petname)

        return tag

    def __str__(self) -> str:
        return f"[{self.pubkey}, {self.relay_url}, {self.petname}]"


class ContactList:
    _list: dict[crypto.PublicKeyStr, ContactInfo]

    def __init__(
        self, init_contacts: typing.Optional[typing.Iterable[ContactInfo]] = None
    ):
        if not init_contacts:
            init_contacts = []

        self._list = dict((ci.pubkey, ci) for ci in init_contacts)

    def add(self, pubkey: crypto.PublicKeyStr, relay_url: str = "", petname: str = ""):
        self._list[pubkey] = ContactInfo(pubkey, relay_url, petname)

    def remove(self, pubkey: crypto.PublicKeyStr):
        del self._list[pubkey]

    def __get_item__(self, pubkey: crypto.PublicKeyStr) -> ContactInfo:
        return self._list[pubkey]

    def __iter__(self) -> typing.Iterator[ContactInfo]:
        return iter(self._list.values())

    def __eq__(self, other) -> bool:
        if isinstance(other, ContactList):
            return self._list == other._list
        return False

    def __repr__(self) -> str:
        return str(list(self._list.values()))
