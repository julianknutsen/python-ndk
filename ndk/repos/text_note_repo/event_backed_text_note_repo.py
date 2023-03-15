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

from ndk import crypto
from ndk.event import event, text_note_event
from ndk.repos.event_repo import event_repo
from ndk.repos.text_note_repo import text_note_repo


class EventBackedTextNoteRepo(text_note_repo.TextNoteRepo):
    _event_repo: event_repo.EventRepo

    def __init__(self, ev_repo: event_repo.EventRepo):
        self._event_repo = ev_repo

    def add(self, keys: crypto.KeyPair, content: str) -> text_note_repo.TextNoteID:
        ev = text_note_event.TextNoteEvent.from_content(content)

        ev_id = self._event_repo.add(event.build_signed_event(ev, keys))
        return text_note_repo.TextNoteID(ev_id)

    def get_by_uid(
        self, uid: text_note_repo.TextNoteID
    ) -> text_note_repo.TextNoteContent:
        signed_event = self._event_repo.get(uid)

        if not signed_event:
            raise ValueError(f"TextNote with uid: {uid} not found.")

        return text_note_repo.TextNoteContent(
            text_note_event.TextNoteEvent.from_signed_event(signed_event).content
        )

    def get_by_author(
        self, author: crypto.PublicKeyStr
    ) -> typing.Sequence[text_note_repo.TextNoteContent]:
        unsigned_events = self._event_repo.get_by_author(
            event.EventKind.TEXT_NOTE, author
        )

        return [text_note_repo.TextNoteContent(ev.content) for ev in unsigned_events]
