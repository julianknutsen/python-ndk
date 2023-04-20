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
# https://github.com/nostr-protocol/nips/blob/master/33.md

import dataclasses
import typing

from ndk.event import event


@dataclasses.dataclass
class ParameterizedReplaceableEvent(event.ReplaceableEvent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self):
        if not 30000 <= self.kind < 40000:
            raise ValueError(
                "ParameterizedReplaceableEvent must be in range [20000-30000)"
            )

        return super().validate()

    def get_normalized_d_tag_value(self) -> typing.Optional[str]:
        """Implement NIP-33 behavior to normalize d tags across variants"""
        tags = self.tags.get("d")
        if len(tags) == 0:
            return None

        if tags[0][1] == "":
            return None

        return tags[0][1]
