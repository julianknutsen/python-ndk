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

from ndk import exceptions, serialize
from ndk.messages import (
    auth,
    close,
    command_result,
    eose,
    event_message,
    message,
    notice,
    relay_event,
    request,
)


def from_str(data: str) -> message.Message:
    lst = serialize.deserialize_str(data)

    if not isinstance(lst, list):
        raise exceptions.ParseError("Expected list, got: {obj}")

    if len(lst) < 2:
        raise exceptions.ParseError("Cant parse data of length < 2")

    hdr = lst[0]

    if hdr == "EVENT":
        if len(lst) > 2:
            # assume RelayEvent
            return relay_event.RelayEvent.deserialize_list(lst)
        else:
            return event_message.Event.deserialize_list(lst)

    factories: dict[str, typing.Type[message.ReadableMessage]] = {
        "NOTICE": notice.Notice,
        "OK": command_result.CommandResult,
        "EOSE": eose.EndOfStoredEvents,
        "EVENT": relay_event.RelayEvent,
        "REQ": request.Request,
        "CLOSE": close.Close,
        "AUTH": auth.Auth,
    }

    if hdr not in factories:
        raise exceptions.ParseError(f"Unknown message type: {hdr}")

    return factories[hdr].deserialize_list(lst)
