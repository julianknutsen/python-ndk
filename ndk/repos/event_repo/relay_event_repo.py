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

"""Implementation of an EventRepo that is backed by a single Relay.

Typical usage example::
    keys = crypto.KeyPair()
    repo = RelayEventRepo(send_fn, recv_fn)
    event_id = repo.add(keys, <UnsignedEvent>)
    event = repo.get(event_id)
"""

import logging
import typing
import uuid

from ndk import crypto
from ndk.event import event, event_parser, request
from ndk.messages import (
    close,
    command_result,
    eose,
    message_factory,
    notice,
    relay_event,
)
from ndk.repos.event_repo import event_repo

SendFn = typing.Callable[[str], int]
RecvFn = typing.Callable[[], str]
SubID = typing.NewType("SubID", str)


class _StoredEvents:
    _events: list[event.UnsignedEvent]
    _complete: bool = False

    def __init__(self):
        self._events = []

    def get(self) -> typing.Sequence[event.UnsignedEvent]:
        assert self._complete, "cant access results before processing complete"
        return self._events

    def process_token(self, token: str) -> bool:
        assert not self._complete, "should not call process_token after complete"

        msg = message_factory.from_str(token)

        if isinstance(msg, eose.EndOfStoredEvents):
            self._complete = True
            return True

        if isinstance(msg, notice.Notice):
            raise RuntimeError(f"NOTICE response from server: {msg.message}")

        if not isinstance(msg, relay_event.RelayEvent):
            raise RuntimeError(f"Unhandled message type: {msg}")

        self._events.append(
            event_parser.signed_to_unsigned(event.SignedEvent(**msg.event_dict))
        )
        return False


class RelayEventRepo(event_repo.EventRepo):
    """Concrete implementation of EventRepo that delegates to a single Relay.
    This class handles the nostr protocol messages between the client
    and server to add new events and get existing events.
    """

    _send_fn: SendFn
    _recv_fn: RecvFn

    def __init__(self, send_fn: SendFn, recv_fn: RecvFn):
        """Initialize

        Args:
            send_fn (SendFn): function that can be called to send a string to a Relay
            recv_fn (RecvFn): function that can be called to receive the next string from a Relay
        """
        self._send_fn = send_fn
        self._recv_fn = recv_fn
        super().__init__()

    def _send_str(self, s: str):
        logging.debug("Sending: %s", s)
        self._send_fn(s)

    def _read_str(self) -> str:
        s = self._recv_fn()
        logging.debug("Received: %s", s)
        return s

    def _write_str_sync(self, serialized: str) -> command_result.CommandResult:
        self._send_str(serialized)
        msg = message_factory.from_str(self._read_str())
        assert isinstance(msg, command_result.CommandResult)
        return msg

    def add(self, signed_ev: event.SignedEvent) -> event.EventID:
        result = self._write_str_sync(signed_ev.serialize())

        if not result.accepted:
            logging.debug("Failed adding event to relay: %s", result.message)
            raise event_repo.AddItemError(
                f"Failed to add {signed_ev}: {result.message}"
            )

        if "duplicate" in result.message:
            logging.debug("Duplicate event sent to relay: %s", result.message)

        return event.EventID(result.event_id)

    def _write_req_msg_sync(
        self,
        fltrs: list[dict],
    ) -> typing.Sequence[event.UnsignedEvent]:
        sub_id = str(uuid.uuid4())
        req = request.Request(sub_id, fltrs)
        serialized = req.serialize()

        self._send_str(serialized)
        stored = _StoredEvents()

        while not stored.process_token(self._read_str()):
            continue

        serialized = close.Close(sub_id).serialize()
        self._send_str(serialized)

        return stored.get()

    def get(self, ev_id: event.EventID) -> event.UnsignedEvent:
        event_itr = self._write_req_msg_sync([{"ids": [ev_id]}])

        events = list(event_itr)

        if not events:
            raise event_repo.GetItemError("No event returned from query for {ev_id}")

        if len(events) > 1:
            raise event_repo.GetItemError(
                f"Expected a single stored event, but received: {events}"
            )

        return events[0]

    def get_by_author(
        self,
        kind: event.EventKind,
        author: crypto.PublicKeyStr,
        limit: int = 0,
    ) -> typing.Sequence[event.UnsignedEvent]:
        fltr = {
            "kinds": [kind],
            "authors": [author],
        }

        if limit:
            fltr["limit"] = limit

        return self._write_req_msg_sync([fltr])
