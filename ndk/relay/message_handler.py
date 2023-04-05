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
from ndk.event import event, event_filter
from ndk.messages import (
    close,
    command_result,
    eose,
    event_message,
    relay_event,
    request,
)
from ndk.relay import event_handler, subscription_handler
from ndk.relay.event_repo import event_repo

logger = logging.getLogger(__name__)


class MessageHandler:
    _repo: event_repo.EventRepo
    _subscription_handler: subscription_handler.SubscriptionHandler
    _event_handler: event_handler.EventHandler

    def __init__(
        self,
        repo: event_repo.EventRepo,
        sh: subscription_handler.SubscriptionHandler,
        eh: event_handler.EventHandler,
    ):
        self._repo = repo
        self._subscription_handler = sh
        self._event_handler = eh

    async def handle_event_message(self, msg: event_message.Event) -> list[str]:
        try:
            signed_ev = event.SignedEvent.from_dict(msg.event_dict)
            await self._event_handler.handle_event(signed_ev)
            return [command_result.CommandResult(signed_ev.id, True, "").serialize()]
        except exceptions.ValidationError:
            text = f"Event validation failed: {msg}"
            logger.info(text, exc_info=True)
            ev_id = msg.event_dict["id"]  # guaranteed if passed Type check above
            return [command_result.CommandResult(ev_id, False, text).serialize()]

    async def handle_close(self, msg: close.Close) -> list[str]:
        self._subscription_handler.clear_filters(msg.sub_id)
        return []

    async def handle_request(self, msg: request.Request) -> list[str]:
        fltrs = [event_filter.EventFilter.from_dict(fltr) for fltr in msg.filter_list]
        fetched = await self._repo.get(fltrs)
        self._subscription_handler.set_filters(msg.sub_id, fltrs)

        return [
            relay_event.RelayEvent(msg.sub_id, ev.__dict__).serialize()
            for ev in fetched
        ] + [eose.EndOfStoredEvents(msg.sub_id).serialize()]
