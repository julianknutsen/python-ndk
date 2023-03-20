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

from ndk.messages import message

REJECTED_MSG_PREFIXES = ["blocked:", "invalid:", "pow:", "rate-limited:", "error:"]


@dataclasses.dataclass
class CommandResult(message.ReadableMessage):
    event_id: str
    accepted: bool
    message: str

    def __post_init__(self):
        super().__post_init__()

        if not self.accepted and not self.message:
            raise TypeError(f"Unexpected empty message {self}")

        if self.accepted and any(
            self.message.startswith(prefix) for prefix in REJECTED_MSG_PREFIXES
        ):
            raise TypeError(f"Unexpected message for accepted status {self}")

    def is_success(self) -> bool:
        return self.accepted

    @classmethod
    def deserialize_list(cls, lst: list):
        assert len(lst) > 0
        assert lst[0] == "OK"

        if len(lst) != 4:
            raise TypeError(
                f"Unexpected format of CommandResult message. Expected four items, but got: {lst}"
            )

        return cls(*lst[1:])
