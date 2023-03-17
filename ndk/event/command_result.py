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

from ndk.event import event, serialize

REJECTED_MSG_PREFIXES = ["blocked:", "invalid:", "pow:", "rate-limited:", "error:"]


@dataclasses.dataclass
class CommandResult:
    event_id: event.EventID
    accepted: bool
    message: str

    def __post_init__(self):
        if not isinstance(self.event_id, event.EventID.__supertype__):  # type: ignore
            raise ValueError(f"Unexpected type for event_id {self.event_id}:{self}")

        if not isinstance(self.accepted, bool):
            raise ValueError(f"Unexpected type for accepted {self.accepted}:{self}")

        if not isinstance(self.message, str):
            raise ValueError(f"Unexpected type for message {self.message}:{self}")

        if not self.message:
            raise ValueError(f"Unexpected empty message {self}")

        if self.accepted and any(
            self.message.startswith(prefix) for prefix in REJECTED_MSG_PREFIXES
        ):
            raise ValueError(f"Unexpected message for accepted status {self}")

    def is_success(self) -> bool:
        return self.accepted

    @classmethod
    def deserialize(cls, s: str):
        obj = serialize.deserialize(s)

        if not isinstance(obj, list):
            raise ValueError(
                f"Unexpected object type for CommandResult: {type(obj)}: {obj}"
            )

        if obj[0] == "NOTICE":
            raise ValueError(f"NOTICE response from server: {obj[1]}")

        if obj[0] != "OK":
            raise ValueError(
                f"Command result requires 'OK' as first element, got {obj[0]}"
            )

        if len(obj) != 4:
            raise ValueError("Unexpected object length. Expected 4, got: {obj}")

        return cls(*obj[1:])
