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

from ndk.event import (
    contact_list_event,
    event,
    metadata_event,
    reaction_event,
    recommend_server_event,
    repost_event,
    text_note_event,
)

LOOKUP: dict[event.EventKind, typing.Type[event.UnsignedEvent]] = {
    event.EventKind.SET_METADATA: metadata_event.MetadataEvent,
    event.EventKind.RECOMMEND_SERVER: recommend_server_event.RecommendServerEvent,
    event.EventKind.TEXT_NOTE: text_note_event.TextNoteEvent,
    event.EventKind.CONTACT_LIST: contact_list_event.ContactListEvent,
    event.EventKind.REPOST: repost_event.RepostEvent,
    event.EventKind.REACTION: reaction_event.ReactionEvent,
}


def signed_to_unsigned(signed_event: event.SignedEvent) -> event.UnsignedEvent:
    if signed_event.kind not in LOOKUP:
        raise ValueError(f"Attempting to parse an unknown event {signed_event}")

    return LOOKUP[signed_event.kind].from_signed_event(signed_event)
