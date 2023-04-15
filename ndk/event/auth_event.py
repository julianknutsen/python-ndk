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
import time

from ndk import crypto, types
from ndk.event import event, event_tags


@dataclasses.dataclass
class AuthEvent(event.Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self):
        if self.kind != types.EventKind.AUTH:
            raise ValueError(f"AuthEvent must have kind {types.EventKind.AUTH}")

        now = int(time.time())
        if abs(now - self.created_at) > 600:
            raise ValueError("AuthEvent must be created within 10 minutes of now")

        relay_tag = self.tags.get("relay")
        if relay_tag == []:
            raise ValueError("AuthEvent must have a relay tag")

        challenge_tag = self.tags.get("challenge")
        if challenge_tag == []:
            raise ValueError("AuthEvent must have a challenge tag")

        return super().validate()

    @classmethod
    def from_parts(
        cls,
        keys: crypto.KeyPair,
        relay_url: str,
        relay_challenge: str,
    ):
        return cls.build(
            keys=keys,
            kind=types.EventKind.AUTH,
            tags=event_tags.EventTags(
                [
                    event_tags.AuthRelayTag.from_relay_url(relay_url),
                    event_tags.AuthChallengeTag.from_challenge(relay_challenge),
                ]
            ),
        )
