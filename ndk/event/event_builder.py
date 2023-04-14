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
from ndk.event import (
    contact_list_event,
    event,
    event_tags,
    metadata_event,
    reaction_event,
    recommend_server_event,
    repost_event,
    text_note_event,
)

LOOKUP: dict[types.EventKind, typing.Type[event.Event]] = {
    types.EventKind.SET_METADATA: metadata_event.MetadataEvent,
    types.EventKind.RECOMMEND_SERVER: recommend_server_event.RecommendServerEvent,
    types.EventKind.TEXT_NOTE: text_note_event.TextNoteEvent,
    types.EventKind.CONTACT_LIST: contact_list_event.ContactListEvent,
    types.EventKind.REPOST: repost_event.RepostEvent,
    types.EventKind.REACTION: reaction_event.ReactionEvent,
}

REQUIRED_FIELDS = set(["id", "pubkey", "created_at", "kind", "tags", "content", "sig"])


def from_dict(fields: dict, skip_validate=False):
    actual = set(fields.keys())
    if not REQUIRED_FIELDS == actual:
        raise ValueError(
            f"Required attributes not provided: {REQUIRED_FIELDS} != {actual}"
        )

    if fields["kind"] not in LOOKUP:
        raise ValueError(f"Unknown event kind: {fields['kind']}")

    return LOOKUP[fields["kind"]](
        id=types.EventID(fields["id"]),
        pubkey=crypto.PublicKeyStr(fields["pubkey"]),
        created_at=fields["created_at"],
        kind=types.EventKind(fields["kind"]),
        tags=event_tags.EventTags(fields["tags"]),
        content=fields["content"],
        sig=crypto.SchnorrSigStr(fields["sig"]),
        skip_validate=skip_validate,
    )


def from_validated_dict(fields: dict):
    return LOOKUP[fields["kind"]](**fields, skip_validate=True)
