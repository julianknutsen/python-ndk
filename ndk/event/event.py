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
import hashlib
import logging
import time
import traceback
import typing

from ndk import crypto, exceptions, serialize, types
from ndk.event import event_tags

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Event:
    id: types.EventID
    pubkey: crypto.PublicKeyStr
    created_at: int
    kind: int
    tags: event_tags.EventTags
    content: str
    sig: crypto.SchnorrSigStr
    skip_validate: dataclasses.InitVar[bool] = False

    def __post_init__(self, skip_validate: bool):
        if not skip_validate:
            self.validate()

    def validate(self):
        if self.kind == types.EventKind.INVALID:
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
    def build(
        cls,
        keys: crypto.KeyPair,
        kind: int,
        tags: typing.Optional[event_tags.EventTags] = None,
        content: typing.Optional[str] = None,
    ):
        created_at = int(time.time())
        if tags is None:
            tags = event_tags.EventTags()
        if content is None:
            content = ""

        payload = serialize.serialize_as_bytes(
            [0, keys.public, created_at, kind, tags, content]
        )

        hashed_payload = hashlib.sha256(payload)
        signed_hash = keys.private.sign_schnorr(hashed_payload.digest())
        return cls(
            id=types.EventID(hashed_payload.hexdigest()),
            pubkey=keys.public,
            kind=kind,
            created_at=created_at,
            tags=tags,
            content=content,
            sig=signed_hash,
            skip_validate=False,
        )


class PersistentEvent:
    """Event should be persisted for later query"""

    pass


class BroadcastEvent:
    """Event shouuld be sent to all subscribers that match filter"""

    pass


class SingletonEvent:
    """Only the latest event of this type and author should exist"""

    pass


class RegularEvent(Event, PersistentEvent, BroadcastEvent):
    pass


class ReplaceableEvent(Event, PersistentEvent, SingletonEvent, BroadcastEvent):
    pass


class EphemeralEvent(Event, BroadcastEvent):
    pass
