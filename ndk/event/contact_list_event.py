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

import dataclasses
import typing

from ndk import crypto, types
from ndk.event import event, event_tags
from ndk.repos import contacts


@dataclasses.dataclass
class ContactListEvent(event.Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_contact_list(
        cls,
        keys: crypto.KeyPair,
        contact_list: typing.Optional[typing.Iterable[contacts.ContactInfo]] = None,
    ) -> "ContactListEvent":
        tags = event_tags.EventTags([])
        if contact_list:
            tags = event_tags.EventTags([ci.to_event_tag() for ci in contact_list])
        return cls.build(keys=keys, kind=types.EventKind.CONTACT_LIST, tags=tags)

    def get_contact_list(self) -> contacts.ContactList:
        return contacts.ContactList(
            [
                contacts.ContactInfo(crypto.PublicKeyStr(pubkey), *rest)
                for _, pubkey, *rest in filter(lambda tag: len(tag) > 1, self.tags)
            ]
        )
