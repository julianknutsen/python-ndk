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

from ndk import crypto, exceptions
from ndk.event import event


def validate_relay_url(relay_url: str):
    if not (relay_url.startswith("ws://") or relay_url.startswith("wss://")):
        raise exceptions.ValidationError(
            f"Relay URL must start with ws:// or ws:// {relay_url}"
        )


class RepostEvent(event.UnsignedEvent):
    @classmethod
    def from_parts(
        cls,
        note_id: event.EventID,
        author: crypto.PublicKeyStr,
        relay_url: str,
        content: str = "",
    ) -> "RepostEvent":
        tags = event.EventTags([["e", note_id, relay_url], ["p", author]])

        return cls(kind=event.EventKind.REPOST, content=content, tags=tags)

    def validate_e_tag(self, e_tag: list[str]):
        if e_tag[0] != "e":
            raise exceptions.ValidationError(
                f"Repost event must have an 'e' tag: {self}"
            )

        event.validate_event_id(e_tag[1])
        validate_relay_url(e_tag[2])

    def validate_p_tag(self, p_tag: list[str]):
        if p_tag[0] != "p":
            raise exceptions.ValidationError(
                f"Repost event w/ 2 tags must have a 'p' tag: {self}"
            )

        crypto.validate_public_key(p_tag[1])

    def validate(self):
        tag_len = len(self.tags)
        if tag_len < 1 or tag_len > 2:
            raise exceptions.ValidationError(
                f"Repost event must have 1 or 2 tags: {self}"
            )

        if tag_len == 1:
            self.validate_e_tag(self.tags[0])
        else:  # tag_len == 2
            if len(self.tags[0]) == 0:
                raise exceptions.ValidationError(f"Repost event has empty tag: {self}")

            if self.tags[0][0] == "e":
                self.validate_e_tag(self.tags[0])
                self.validate_p_tag(self.tags[1])
            else:
                self.validate_p_tag(self.tags[0])
                self.validate_e_tag(self.tags[1])

        return super().validate()
