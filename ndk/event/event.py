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

from ndk import crypto, exceptions, serialize, types
from ndk.event import event_tags

logger = logging.getLogger(__name__)


class EventKind(enum.IntEnum):
    INVALID = -1
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_SERVER = 2
    CONTACT_LIST = 3
    REPOST = 6


@dataclasses.dataclass
class UnsignedEvent:
    created_at: int = dataclasses.field(default_factory=lambda: int(time.time()))
    kind: EventKind = EventKind.INVALID
    tags: event_tags.EventTags = dataclasses.field(
        default_factory=lambda: event_tags.EventTags([])
    )
    content: str = ""
    skip_validate: dataclasses.InitVar[bool] = False

    def __post_init__(self, skip_validate: bool):
        if not skip_validate:
            self.validate()

    def validate(self):
        pass

    @classmethod
    def from_signed_event(cls, ev: "SignedEvent"):
        return cls(ev.created_at, ev.kind, ev.tags, ev.content)


@dataclasses.dataclass
class SignedEvent(UnsignedEvent):
    id: types.EventID = dataclasses.field(init=False)
    pubkey: crypto.PublicKeyStr = dataclasses.field(init=False)
    sig: crypto.SchnorrSigStr = dataclasses.field(init=False)

    def __init__(
        self,
        id: types.EventID,  # pylint: disable=redefined-builtin
        pubkey: crypto.PublicKeyStr,
        created_at: int,
        kind: EventKind,
        tags: event_tags.EventTags,
        content: str,
        sig: crypto.SchnorrSigStr,
        skip_validate: bool = False,
    ):
        self.id = id
        self.pubkey = pubkey
        self.sig = sig

        super().__init__(
            created_at=created_at,
            kind=kind,
            tags=tags,
            content=content,
            skip_validate=skip_validate,
        )

    def __post_init__(self, skip_validate: bool):
        if not skip_validate:
            self.validate()

        super().__post_init__(skip_validate)

    def validate(self):
        valid_kinds = [kind.value for kind in EventKind if kind != EventKind.INVALID]
        if self.kind not in valid_kinds:
            raise exceptions.ValidationError(f"Invalid event kind {self.kind}")

        payload = serialize.serialize_as_bytes(
            [0, self.pubkey, self.created_at, self.kind, self.tags, self.content]
        )

        hashed_payload = hashlib.sha256(payload)

        try:
            if not self.sig.verify(self.pubkey, hashed_payload.digest()):
                raise exceptions.ValidationError(
                    f"Signature in event did not match PublicKey: {self}"
                )
        except Exception as exc:
            logger.debug(traceback.format_exc())
            raise exceptions.ValidationError(
                f"Signature validation failed: {self}"
            ) from exc

        if hashed_payload.hexdigest() != self.id:
            raise exceptions.ValidationError(
                f"ID does not match hash of payload: {self}"
            )

    @classmethod
    def from_dict(cls, fields: dict):
        required = set(cls.__annotations__.keys())
        for base_cls in cls.__bases__:
            required.update(base_cls.__annotations__)
        required.remove("skip_validate")
        actual = set(fields.keys())
        if not required == actual:
            raise exceptions.ParseError(
                f"Required attributes not provided: {required} != {actual}"
            )

        return cls(
            id=types.EventID(fields["id"]),
            pubkey=crypto.PublicKeyStr(fields["pubkey"]),
            created_at=fields["created_at"],
            kind=EventKind(fields["kind"]),
            tags=event_tags.EventTags(fields["tags"]),
            content=fields["content"],
            sig=crypto.SchnorrSigStr(fields["sig"]),
        )

    @classmethod
    def from_validated_dict(cls, fields: dict):
        return cls(**fields, skip_validate=True)


def build_signed_event(ev: UnsignedEvent, keys: crypto.KeyPair) -> SignedEvent:
    payload = serialize.serialize_as_bytes(
        [0, keys.public, ev.created_at, ev.kind, ev.tags, ev.content]
    )

    hashed_payload = hashlib.sha256(payload)
    signed_hash = keys.private.sign_schnorr(hashed_payload.digest())

    return SignedEvent(
        types.EventID(hashed_payload.hexdigest()),
        keys.public,
        ev.created_at,
        ev.kind,
        ev.tags,
        ev.content,
        signed_hash,
    )
