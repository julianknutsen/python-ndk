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
import enum
import hashlib
import time
import typing

from ndk import crypto, serialize

EventTags = typing.NewType("EventTags", list[list[str]])
EventID = typing.NewType("EventID", str)


class EventKind(enum.IntEnum):
    INVALID = -1
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_SERVER = 2
    CONTACT_LIST = 3


@dataclasses.dataclass(frozen=True)
class UnsignedEvent:
    created_at: int = dataclasses.field(default_factory=lambda: int(time.time()))
    tags: EventTags = dataclasses.field(default_factory=lambda: EventTags([[]]))
    content: str = ""
    kind: EventKind = EventKind.INVALID

    @classmethod
    def from_signed_event(cls, ev: "SignedEvent"):
        return cls(ev.created_at, ev.tags, ev.content, ev.kind)


@dataclasses.dataclass(frozen=True)
class SignedEvent(UnsignedEvent):
    id: EventID = dataclasses.field(init=False)
    pubkey: crypto.PublicKeyStr = dataclasses.field(init=False)
    sig: crypto.SchnorrSigStr = dataclasses.field(init=False)

    def __init__(
        self,
        id: EventID,  # pylint: disable=redefined-builtin
        pubkey: crypto.PublicKeyStr,
        created_at: int,
        kind: EventKind,
        tags: EventTags,
        content: str,
        sig: crypto.SchnorrSigStr,
    ):
        super().__init__(created_at, tags, content)

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "pubkey", pubkey)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "sig", sig)


def _validate_unsigned_event(ev: UnsignedEvent):
    now = int(time.time())
    if ev.created_at > now:
        raise ValueError(
            f"UnsignedEvent created_at timestamp must be in the past: {ev.created_at} >= {now}"  # pylint: disable=line-too-long
        )


def build_signed_event(ev: UnsignedEvent, keys: crypto.KeyPair) -> SignedEvent:
    _validate_unsigned_event(ev)

    payload = serialize.serialize_as_bytes(
        [0, keys.public, ev.created_at, ev.kind, ev.tags, ev.content]
    )

    hashed_payload = hashlib.sha256(payload)
    signed_hash = keys.private.sign_schnorr(hashed_payload.digest())

    return SignedEvent(
        EventID(hashed_payload.hexdigest()),
        keys.public,
        ev.created_at,
        ev.kind,
        ev.tags,
        ev.content,
        signed_hash,
    )
