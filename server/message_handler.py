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

import logging

from ndk import exceptions
from ndk.event import event
from ndk.messages import (
    close,
    command_result,
    eose,
    event_message,
    message,
    message_factory,
    notice,
    relay_event,
    request,
)

logger = logging.getLogger(__name__)


def create_notice(text: str) -> str:
    return notice.Notice(text).serialize()


def create_cmd_result(ev_id: str, accepted: bool, msg: str) -> str:
    return command_result.CommandResult(ev_id, accepted, msg).serialize()


def create_relay_event(sub_id: str, ev_dict: dict) -> str:
    return relay_event.RelayEvent(sub_id, ev_dict).serialize()


def create_eose(sub_id: str) -> str:
    return eose.EndOfStoredEvents(sub_id).serialize()


class MessageHandler:
    _stored_events: list[event.SignedEvent]

    def __init__(self):
        self._stored_events = []

    def process_message(self, data: str) -> list[str]:
        try:
            msg = message_factory.from_str(data)
            return self._handle_msg(msg)
        except exceptions.ParseError:
            text = f"Unable to parse message: {data}"
            logger.debug(text, exc_info=True)
            return [create_notice(text)]

    def _handle_msg(self, msg: message.Message) -> list[str]:
        if isinstance(msg, event_message.Event):
            return self._handle_event(msg)
        elif isinstance(msg, request.Request):
            return self._handle_request(msg)
        elif isinstance(msg, close.Close):
            return self._handle_close(msg)
        else:
            return [create_notice(f"Server does not support message of type: {msg}")]

    def _handle_event(self, msg: event_message.Event) -> list[str]:
        try:
            signed_ev = event.SignedEvent.from_dict(msg.event_dict)

            self._stored_events.append(signed_ev)

            return [create_cmd_result(signed_ev.id, True, "")]
        except event.ValidationError:
            text = f"Event validation failed: {msg}"
            logger.debug(text, exc_info=True)
            ev_id = msg.event_dict["id"]  # guaranteed if passed Type check above
            return [create_cmd_result(ev_id, False, text)]

    def _handle_close(self, _: close.Close) -> list[str]:
        return []

    def _handle_request(self, msg: request.Request) -> list[str]:
        fetched: list[event.SignedEvent] = []

        for fltr in msg.filter_list:
            # only id fetch
            if set(["ids"]) == set(fltr.keys()):
                for ev_id in fltr["ids"]:
                    for ev in self._stored_events:
                        if ev.id == ev_id:
                            fetched.append(ev)

            # search by kind & author
            elif set(["kinds", "authors", "limit"]) == set(fltr.keys()) or set(
                ["kinds", "authors"]
            ) == set(fltr.keys()):
                limit = 0
                if "limit" in fltr:
                    limit = fltr["limit"]

                fetched = sorted(
                    [
                        ev
                        for ev in self._stored_events
                        if ev.kind in fltr["kinds"] and ev.pubkey in fltr["authors"]
                    ],
                    key=lambda ev: ev.created_at,
                )[-limit:]
        return [create_relay_event(msg.sub_id, ev.__dict__) for ev in fetched] + [
            create_eose(msg.sub_id)
        ]
