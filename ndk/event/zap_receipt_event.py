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
# https://github.com/nostr-protocol/nips/blob/master/57.md

import dataclasses

from ndk import types
from ndk.event import event


@dataclasses.dataclass
class ZapReceiptEvent(event.Event):
    """NIP-57 Zap Receipt Event"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self):
        if self.kind != types.EventKind.ZAP_RECEIPT:
            raise ValueError(
                f"ZapReceiptEvent must have kind {types.EventKind.ZAP_RECEIPT}"
            )

        if self.content != "":
            raise ValueError("ZapReceiptEvent must have empty content")

        for identifier in ["p", "bolt11", "description"]:
            relay_tag = self.tags.get(identifier)
            if relay_tag == []:
                raise ValueError(f"ZapReceiptEvent must have a {identifier} tag")

        return super().validate()
