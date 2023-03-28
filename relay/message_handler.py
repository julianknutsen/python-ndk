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

from ndk.event import event, event_filter
from ndk.messages import (
    close,
    command_result,
    eose,
    event_message,
    relay_event,
    request,
)
from relay.event_repo import event_repo

logger = logging.getLogger(__name__)


def create_cmd_result(ev_id: str, accepted: bool, msg: str) -> str:
    return command_result.CommandResult(ev_id, accepted, msg).serialize()


def create_relay_event(sub_id: str, ev_dict: dict) -> str:
    return relay_event.RelayEvent(sub_id, ev_dict).serialize()


def create_eose(sub_id: str) -> str:
    return eose.EndOfStoredEvents(sub_id).serialize()


class MessageHandler:
    _repo: event_repo.EventRepo

    def __init__(self, repo: event_repo.EventRepo):
        self._repo = repo

    async def handle_event(self, msg: event_message.Event) -> list[str]:
        try:
            signed_ev = event.SignedEvent.from_dict(msg.event_dict)

            await self._repo.add(signed_ev)

            return [create_cmd_result(signed_ev.id, True, "")]
        except event.ValidationError:
            text = f"Event validation failed: {msg}"
            logger.debug(text, exc_info=True)
            ev_id = msg.event_dict["id"]  # guaranteed if passed Type check above
            return [create_cmd_result(ev_id, False, text)]

    async def handle_close(self, _: close.Close) -> list[str]:
        return []

    async def handle_request(self, msg: request.Request) -> list[str]:
        fetched = await self._repo.get(
            [event_filter.EventFilter.from_dict(fltr) for fltr in msg.filter_list]
        )

        return [create_relay_event(msg.sub_id, ev.__dict__) for ev in fetched] + [
            create_eose(msg.sub_id)
        ]
