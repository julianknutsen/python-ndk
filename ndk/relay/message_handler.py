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
import functools
import logging

from ndk import exceptions
from ndk.event import event_builder, event_filter
from ndk.messages import (
    auth,
    close,
    command_result,
    eose,
    event_message,
    notice,
    relay_event,
    request,
)
from ndk.relay import auth_handler, event_handler, subscription_handler
from ndk.relay.event_repo import event_repo

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class MessageHandlerConfig:
    max_filters: int = 100
    max_limit: int = 5000
    min_prefix: int = 4


# Race condition between handling AUTH and handling first message. This decorator
# will attempt to wait for the auth to process.
def authentication_retry():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except PermissionError:
                await self._auth.wait_for_authenticated(  # pylint: disable=protected-access
                    timeout=5
                )
                return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def create_notice(text: str) -> str:
    return notice.Notice(text).serialize()


class MessageHandler:
    _auth: auth_handler.AuthHandler
    _cfg: MessageHandlerConfig
    _event_handler: event_handler.EventHandler
    _repo: event_repo.EventRepo
    _subscription_handler: subscription_handler.SubscriptionHandler

    def __init__(
        self,
        auth_hndlr: auth_handler.AuthHandler,
        repo: event_repo.EventRepo,
        sh: subscription_handler.SubscriptionHandler,
        eh: event_handler.EventHandler,
        cfg: MessageHandlerConfig = MessageHandlerConfig(),
    ):
        self._auth = auth_hndlr
        self._cfg = cfg
        self._event_handler = eh
        self._repo = repo
        self._subscription_handler = sh

    async def handle_event_message(self, msg: event_message.Event) -> list[str]:
        try:
            ev = event_builder.from_dict(msg.event_dict)
            await self._event_handler.handle_event(ev)
            return [command_result.CommandResult(ev.id, True, "").serialize()]
        except exceptions.ValidationError as exc:
            text = f"Event validation failed: {exc.args[0]} {msg}"
            logger.info(text, exc_info=True)
            ev_id = msg.event_dict["id"]  # guaranteed if passed Type check above
            return [command_result.CommandResult(ev_id, False, text).serialize()]

    async def handle_close(self, msg: close.Close) -> list[str]:
        await self._subscription_handler.clear_filters(msg.sub_id)
        return []

    @authentication_retry()
    async def handle_request(self, msg: request.Request) -> list[str]:
        if len(msg.filter_list) > self._cfg.max_filters:
            return [
                create_notice(
                    f"Relay does not support more than {self._cfg.max_filters} filters."
                )
            ]

        fltrs = []
        for d in msg.filter_list:
            fltr = event_filter.AuthenticatedEventFilter.from_dict_and_auth_pubkey(
                d, self._auth.authenticated_pubkey()
            )

            if fltr.ids and any(len(val) < self._cfg.min_prefix for val in fltr.ids):
                return [
                    create_notice(
                        f"Relay does not support filters with id prefixes shorter than {self._cfg.min_prefix} characters."
                    )
                ]

            if fltr.authors and any(
                len(val) < self._cfg.min_prefix for val in fltr.authors
            ):
                return [
                    create_notice(
                        f"Relay does not support filters with author prefixes shorter than {self._cfg.min_prefix} characters."
                    )
                ]

            if fltr.limit and fltr.limit > self._cfg.max_limit:
                return [
                    create_notice(
                        f"Relay does not support filters with a limit greater than {self._cfg.max_limit}."
                    )
                ]

            fltrs.append(fltr)

        fetched = await self._repo.get(fltrs)
        await self._subscription_handler.set_filters(msg.sub_id, fltrs)

        return [
            relay_event.RelayEvent(msg.sub_id, ev.__dict__).serialize()
            for ev in fetched
        ] + [eose.EndOfStoredEvents(msg.sub_id).serialize()]

    async def handle_auth_response(self, msg: auth.AuthResponse) -> list[str]:
        self._auth.handle_auth_event(msg.ev)
        logger.debug("Client authenticated")
        return []
