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
import logging
import time
import traceback
import typing

from ndk import crypto, exceptions, serialize

logger = logging.getLogger(__name__)


EventTags = typing.NewType("EventTags", list[list[str]])
EventID = typing.NewType("EventID", str)


class ValidationError(ValueError):
    pass


class EventKind(enum.IntEnum):
    INVALID = -1
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_SERVER = 2
    CONTACT_LIST = 3


@dataclasses.dataclass
class UnsignedEvent:
    created_at: int = dataclasses.field(default_factory=lambda: int(time.time()))
    kind: EventKind = EventKind.INVALID
    tags: EventTags = dataclasses.field(default_factory=lambda: EventTags([[]]))
    content: str = ""

    def __post_init__(self):
        now = int(time.time())
        if self.created_at > now:
            raise ValueError(
                f"UnsignedEvent created_at timestamp must be in the past: {self.created_at} >= {now}"  # pylint: disable=line-too-long
            )

    @classmethod
    def from_signed_event(cls, ev: "SignedEvent"):
        return cls(ev.created_at, ev.kind, ev.tags, ev.content)


@dataclasses.dataclass
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
        self.id = id
        self.pubkey = pubkey
        self.sig = sig

        super().__init__(created_at=created_at, kind=kind, tags=tags, content=content)

    def __post_init__(self):
        payload = serialize.serialize_as_bytes(
            [0, self.pubkey, self.created_at, self.kind, self.tags, self.content]
        )

        hashed_payload = hashlib.sha256(payload)

        try:
            if not crypto.verify_signature(
                self.pubkey, self.sig, hashed_payload.digest()
            ):
                raise ValidationError(
                    f"Signature in event did not match PublicKey: {self}"
                )
        except Exception as exc:
            logger.debug(traceback.format_exc())
            raise ValidationError(f"Signature validation failed: {self}") from exc

        if not hashed_payload.hexdigest() == self.id:
            raise ValidationError(f"ID does not match hash of payload: {self}")

    @classmethod
    def from_dict(cls, fields: dict):
        required = set(cls.__annotations__.keys())
        for base_cls in cls.__bases__:
            required.update(base_cls.__annotations__)
        actual = set(fields.keys())
        if not required == actual:
            raise exceptions.ParseError(
                f"Required attributes not provided: {required} != {actual}"
            )

        return cls(**fields)


def build_signed_event(ev: UnsignedEvent, keys: crypto.KeyPair) -> SignedEvent:
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
