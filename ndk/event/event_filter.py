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
import typing

from ndk.event import event

# "ids": <a list of event ids or prefixes>,
# "authors": <a list of pubkeys or prefixes, the pubkey of an event must be one of these>,
# "kinds": <a list of a kind numbers>,
# "#e": <a list of event ids that are referenced in an "e" tag>,
# "#p": <a list of pubkeys that are referenced in a "p" tag>,
# "since": <an integer unix timestamp, events must be newer than this to pass>,
# "until": <an integer unix timestamp, events must be older than this to pass>,
# "limit": <maximum number of events to be returned in the initial query>


@dataclasses.dataclass
class EventFilter:
    ids: typing.Optional[list[str]] = None
    authors: typing.Optional[list[str]] = None
    kinds: typing.Optional[list[int]] = None
    e_tags: typing.Optional[list[str]] = None
    p_tags: typing.Optional[list[str]] = None
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
                raise ValueError(f"{field_name} must be a list of lst_val_type")

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
        if self.e_tags is not None:
            self.check_list("e_tags", str)
            self.set_falsy_to_none("e_tags")
        if self.p_tags is not None:
            self.check_list("p_tags", str)
            self.set_falsy_to_none("p_tags")
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
            if self.limit <= 0:
                raise ValueError("Limit must be greater than 0")

    def for_req(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if v is not None:
                if k == "e_tags":
                    d["#e"] = v
                elif k == "p_tags":
                    d["#p"] = v
                else:
                    d[k] = v
        return d

    def matches_event(self, ev: event.SignedEvent) -> bool:
        if self.ids and ev.id not in self.ids:
            return False

        if self.authors and ev.pubkey not in self.authors:
            return False

        if self.kinds and ev.kind not in self.kinds:
            return False

        if self.e_tags or self.p_tags and ev.tags:
            ev_tags = collections.defaultdict(list)
            for tag in ev.tags:
                if not tag:
                    continue

                if tag[0] == "e":
                    ev_tags["e"].append(tag[1])
                elif tag[0] == "p":
                    ev_tags["p"].append(tag[1])

            if self.e_tags:
                if "e" not in ev_tags:
                    return False
                elif not any(t in ev_tags["e"] for t in self.e_tags):
                    return False

            if self.p_tags:
                if "p" not in ev_tags:
                    return False
                elif not any(t in ev_tags["p"] for t in self.p_tags):
                    return False

        if self.until and ev.created_at >= self.until:
            return False

        if self.since and ev.created_at <= self.since:
            return False

        return True

    @classmethod
    def from_dict(cls, d: dict) -> "EventFilter":
        return EventFilter(
            ids=d.get("ids"),
            authors=d.get("authors"),
            kinds=d.get("kinds"),
            e_tags=d.get("#e"),
            p_tags=d.get("#p"),
            since=d.get("since"),
            until=d.get("until"),
            limit=d.get("limit"),
        )
