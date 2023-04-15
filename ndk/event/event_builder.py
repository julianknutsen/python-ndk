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

import logging
import typing

from ndk import crypto, types
from ndk.event import (
    auth_event,
    contact_list_event,
    event,
    event_tags,
    metadata_event,
    reaction_event,
    recommend_server_event,
    repost_event,
    text_note_event,
)

logger = logging.getLogger(__name__)

LOOKUP: dict[int, typing.Type[event.Event]] = {
    types.EventKind.SET_METADATA: metadata_event.MetadataEvent,
    types.EventKind.RECOMMEND_SERVER: recommend_server_event.RecommendServerEvent,
    types.EventKind.TEXT_NOTE: text_note_event.TextNoteEvent,
    types.EventKind.CONTACT_LIST: contact_list_event.ContactListEvent,
    types.EventKind.REPOST: repost_event.RepostEvent,
    types.EventKind.REACTION: reaction_event.ReactionEvent,
    types.EventKind.AUTH: auth_event.AuthEvent,
}

REQUIRED_FIELDS = set(["id", "pubkey", "created_at", "kind", "tags", "content", "sig"])


def from_dict(fields: dict, skip_validate=False):
    actual = set(fields.keys())
    if not REQUIRED_FIELDS == actual:
        raise ValueError(
            f"Required attributes not provided: {REQUIRED_FIELDS} != {actual}"
        )

    kind = fields["kind"]
    if kind in LOOKUP:
        builder = LOOKUP[kind]
    elif 1000 <= kind < 10000:
        builder = event.RegularEvent
        logger.warning("Handling unspecified RegularEvent: %s", fields)
    elif 10000 <= kind < 20000:
        builder = event.ReplaceableEvent
        logger.warning("Handling unspecified RepalceableEvent: %s", fields)
    elif 20000 <= kind < 30000:
        builder = event.EphemeralEvent
        logger.warning("Handling unspecified EphemeralEvent: %s", fields)
    else:
        raise ValueError(f"Invalid event kind {kind}")

    return builder(
        id=types.EventID(fields["id"]),
        pubkey=crypto.PublicKeyStr(fields["pubkey"]),
        created_at=fields["created_at"],
        kind=kind,
        tags=event_tags.EventTags(fields["tags"]),
        content=fields["content"],
        sig=crypto.SchnorrSigStr(fields["sig"]),
        skip_validate=skip_validate,
    )


def from_validated_dict(fields: dict):
    return from_dict(fields, skip_validate=True)
