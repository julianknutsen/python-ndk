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


import uuid
from collections import defaultdict

from ndk import crypto
from ndk.event import event
from ndk.repos.text_note_repo import text_note_repo


class FakeTextNoteRepo(text_note_repo.TextNoteRepo):
    _content: dict[str, text_note_repo.TextNoteContent]
    _content_author: dict[crypto.PublicKeyStr, list[text_note_repo.TextNoteContent]]

    def __init__(self):
        self._content = defaultdict()
        self._content_author = defaultdict(list[text_note_repo.TextNoteContent])

    async def add(
        self, keys: crypto.KeyPair, content: str
    ) -> text_note_repo.TextNoteID:
        uid = str(uuid.uuid4())
        self._content[uid] = text_note_repo.TextNoteContent(content)
        self._content_author[keys.public].append(
            text_note_repo.TextNoteContent(content)
        )

        return text_note_repo.TextNoteID(event.EventID(uid))

    async def get_by_uid(
        self, uid: text_note_repo.TextNoteID
    ) -> text_note_repo.TextNoteContent:
        return self._content[uid]

    async def get_by_author(
        self, author: crypto.PublicKeyStr
    ) -> list[text_note_repo.TextNoteContent]:
        return self._content_author[author]
