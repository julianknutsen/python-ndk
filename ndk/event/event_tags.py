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

from ndk import crypto, types


def validate_relay_url(relay_url: str):
    if not (relay_url.startswith("ws://") or relay_url.startswith("wss://")):
        raise ValueError(f"Relay URL must start with ws:// or ws:// {relay_url}")


class EventTag(list):
    def __new__(cls, value: list[str]):
        if not isinstance(value, list):
            raise ValueError(f"{cls.__name__} must be a list, not {type(value)}")

        if len(value) < 2:
            raise ValueError(f"{cls.__name__} must have at least 2 items, not {value}")

        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"{cls.__name__} must be a list of str, not {value}")

        return super().__new__(cls, *value)


class PublicKeyTag(EventTag):
    def __init__(self, value: list[str]):
        if len(value) not in (2, 3):
            raise ValueError(
                f"{self.__class__.__name__} must have 2 or 3 items, not {value}"
            )

        if value[0] != "p":
            raise ValueError(
                f"{self.__class__.__name__} must start with 'p', not {value}"
            )

        crypto.PublicKeyStr.validate(value[1])

        if len(value) == 3:
            validate_relay_url(value[2])

        super().__init__(value)

    @classmethod
    def from_pubkey(cls, pubkey: str, relay_url: typing.Optional[str] = None):
        if relay_url is not None:
            return cls(["p", pubkey, relay_url])
        return cls(["p", pubkey])


class EventIdTag(EventTag):
    def __init__(self, value: list[str]):
        if len(value) not in (2, 3):
            raise ValueError(
                f"{self.__class__.__name__} must have 2 or 3 items, not {value}"
            )

        if value[0] != "e":
            raise ValueError(
                f"{self.__class__.__name__} must start with 'e', not {value}"
            )

        types.EventID.validate(value[1])

        if len(value) == 3:
            validate_relay_url(value[2])

        super().__init__(value)

    @classmethod
    def from_event_id(cls, event_id: str, relay_url: typing.Optional[str] = None):
        if relay_url is not None:
            return cls(["e", event_id, relay_url])
        return cls(["e", event_id])


class UnknownEventTag(EventTag):
    pass


class EventTags(list):
    def __init__(self, tags: typing.Optional[list[list[str]]] = None):
        if tags is None:
            tags = []

        super().__init__()

        if not isinstance(tags, list):
            raise ValueError(
                f"{self.__class__.__name__} must be a str, not {type(tags)}"
            )

        if not all(isinstance(item, list) for item in tags):
            raise ValueError(
                f"{self.__class__.__name__} must be a list of lists, not {tags}"
            )

        for tag in tags:
            if len(tag) < 2:
                raise ValueError(f"Tag must have at least 2 items, not {tag}")

            self.add(self._parse_tag(tag))

    def get(self, identifier: str) -> list[EventTag]:
        return [tag for tag in self if tag[0] == identifier]

    def _parse_tag(self, tag: list[str]) -> EventTag:
        if tag[0] == "p":
            return PublicKeyTag(tag)
        elif tag[0] == "e":
            return EventIdTag(tag)
        else:
            return UnknownEventTag(tag)

    def add(self, tag: EventTag):
        self.append(tag)
