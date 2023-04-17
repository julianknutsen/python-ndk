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

import collections
import dataclasses
import logging
import string
import typing

from ndk import crypto, types
from ndk.event import event

# "ids": <a list of event ids or prefixes>,
# "authors": <a list of pubkeys or prefixes, the pubkey of an event must be one of these>,
# "kinds": <a list of a kind numbers>,
# "#e": <a list of event ids that are referenced in an "e" tag>,
# "#p": <a list of pubkeys that are referenced in a "p" tag>,
# "since": <an integer unix timestamp, events must be newer than this to pass>,
# "until": <an integer unix timestamp, events must be older than this to pass>,
# "limit": <maximum number of events to be returned in the initial query>


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class EventFilter:
    ids: typing.Optional[list[str]] = None
    authors: typing.Optional[list[str]] = None
    kinds: typing.Optional[list[int]] = None
    generic_tags: typing.Optional[dict[str, list[str]]] = None
    since: typing.Optional[int] = None
    until: typing.Optional[int] = None
    limit: typing.Optional[int] = None

    def check_value(self, field_name, val_type):
        if not isinstance(self.__dict__[field_name], val_type):
            raise ValueError(f"{field_name} must be a {val_type}")

    def check_list(self, field_name, lst_val_type):
        self.check_value(field_name, list)

        lst = self.__dict__[field_name]
        if len(lst) > 0:
            if not isinstance(lst[0], lst_val_type):
                raise ValueError(f"{field_name} must be a list of {lst_val_type}")

    def set_falsy_to_none(self, field_name):
        if self.__dict__[field_name] is not None and not self.__dict__[field_name]:
            self.__dict__[field_name] = None

    def __post_init__(self):
        if self.ids is not None:
            self.check_list("ids", str)
            self.set_falsy_to_none("ids")
        if self.authors is not None:
            self.check_list("authors", str)
            self.set_falsy_to_none("authors")
        if self.kinds is not None:
            self.check_list("kinds", int)
            self.set_falsy_to_none("kinds")
        if self.generic_tags is not None:
            if not isinstance(self.generic_tags, dict):
                raise ValueError("generic_tags must be a dict")
            for k, v in self.generic_tags.items():
                if not isinstance(k, str):
                    raise ValueError("generic_tags keys must be strings")
                if len(k) != 1 or k not in string.ascii_letters:
                    raise ValueError("generic_tags keys must be a single letter")
                if not isinstance(v, list):
                    raise ValueError("generic_tags values must be lists")
                for i in v:
                    if not isinstance(i, str):
                        raise ValueError("generic_tags list values must be strings")

            # Remove all empty lists from generic_tags
            to_del = []
            for k, v in self.generic_tags.items():
                if len(v) == 0:
                    to_del.append(k)
            for k in to_del:
                del self.generic_tags[k]

            self.set_falsy_to_none("generic_tags")
        if self.since is not None:
            self.check_value("since", int)
            if self.since < 0:
                raise ValueError("since must be greater than or equal to 0")
        if self.until is not None:
            self.check_value("until", int)
            if self.until <= 0:
                raise ValueError("until must be greater than 0")
        if self.limit is not None:
            self.check_value("limit", int)
            if self.limit < 0:
                raise ValueError("Limit must be greater than or equal to 0")

        if self.kinds is not None:
            for kind in self.kinds:
                if kind not in types.EventKind.__dict__.values():
                    logger.warning(
                        "Creating filter %s w/ unknown event type: %s", self, kind
                    )

    def for_req(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if v is not None:
                if k == "generic_tags":
                    for k2, v2 in v.items():
                        d[f"#{k2}"] = v2
                else:
                    d[k] = v
        return d

    def matches_event(self, ev: event.Event) -> bool:
        if self.ids and not any(ev.id.startswith(x) for x in self.ids):
            return False

        if self.authors and not any(ev.pubkey.startswith(x) for x in self.authors):
            return False

        if self.kinds and ev.kind not in self.kinds:
            return False

        if self.generic_tags:
            if not ev.tags:
                # no tags in ev, but filter requires them
                return False

            ev_tags = collections.defaultdict(list)
            for tag in ev.tags:
                # allow generic queries for all `#[alpha]` based on NIP-12
                if tag[0] in string.ascii_letters:
                    ev_tags[tag[0]].append(tag[1])

            for identifier, lst in self.generic_tags.items():
                if identifier not in ev_tags:
                    # identifier required in filter, but event has no tags w/ identifier
                    return False
                elif not any(val in ev_tags[identifier] for val in lst):
                    # ev has required identifier, but values in filter don't match ev values
                    return False

        if self.until and ev.created_at >= self.until:
            return False

        if self.since and ev.created_at <= self.since:
            return False

        return True

    @classmethod
    def from_dict(cls, d: dict) -> "EventFilter":
        generic_tag_queries = {}
        for c in string.ascii_lowercase:
            key = f"#{c}"
            if key in d:
                generic_tag_queries[c] = d[key]

        return EventFilter(
            ids=d.get("ids"),
            authors=d.get("authors"),
            kinds=d.get("kinds"),
            generic_tags=generic_tag_queries,
            since=d.get("since"),
            until=d.get("until"),
            limit=d.get("limit"),
        )


@dataclasses.dataclass
class AuthenticatedEventFilter(EventFilter):
    @classmethod
    def from_dict_and_auth_pubkey(
        cls, d: dict, auth_pubkey: typing.Optional[crypto.PublicKeyStr]
    ) -> EventFilter:
        fltr = super().from_dict(d)

        # Kind 4 is a special case where we need to restrict clients
        # that can query
        if fltr.kinds and 4 in fltr.kinds:
            if not auth_pubkey:
                raise PermissionError(
                    "Cannot query for kind 4 events without NIP-42 auth"
                )

            # p tag or author must be set
            if (
                not fltr.generic_tags or "p" not in fltr.generic_tags
            ) and not fltr.authors:
                raise PermissionError(
                    "Cannot query for kind 4 events without a receiver or author"
                )

            # receiver can be the auth pubkey
            if (
                fltr.generic_tags
                and "p" in fltr.generic_tags
                and fltr.generic_tags["p"] != [auth_pubkey]
            ):
                raise PermissionError(
                    "Cannot query for kind 4 events with a receiver other than the auth pubkey"
                )

            # or the event can be signed by the auth pubkey
            if fltr.authors and fltr.authors != [auth_pubkey]:
                raise PermissionError(
                    "Cannot query for kind 4 events signed by a pubkey other than the auth pubkey"
                )

        return fltr
