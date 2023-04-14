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

from ndk import crypto, exceptions, types
from ndk.event import event, event_tags


class ReactionEvent(event.Event):
    @classmethod
    def from_text_note_event(
        cls,
        keys: crypto.KeyPair,
        text_note: event.Event,
        content: str = "+",
    ) -> "ReactionEvent":
        tags = event_tags.EventTags()
        tags.extend(text_note.tags.get("e"))
        tags.extend(text_note.tags.get("p"))

        tags.add(event_tags.PublicKeyTag.from_pubkey(text_note.pubkey))
        tags.add(event_tags.EventIdTag.from_event_id(text_note.id))

        return cls.build(
            keys=keys, kind=types.EventKind.REACTION, content=content, tags=tags
        )

    def validate(self):
        if len(self.tags) < 2:
            raise exceptions.ValidationError(
                f"{self.__class__.__name__} must have 2 or more tags: {self}"
            )

        if len(self.tags.get("p")) < 1:
            raise exceptions.ValidationError(
                f"{self.__class__.__name__}  must have one or more 'p' tags: {self}"
            )

        if len(self.tags.get("e")) < 1:
            raise exceptions.ValidationError(
                f"{self.__class__.__name__}  must have one or more 'e' tags: {self}"
            )

        return super().validate()
