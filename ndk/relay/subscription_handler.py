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

import asyncio
import dataclasses
import functools

from ndk.event import event, event_filter
from ndk.messages import relay_event


def locked():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            async with self._lock:  # pylint: disable=protected-access
                return await func(self, *args, **kwargs)

        return wrapper

    return decorator


class ConfigLimitsExceeded(Exception):
    pass


@dataclasses.dataclass
class SubscriptionHandlerConfig:
    max_subscriptions: int = 20
    max_subid_length: int = 100


class SubscriptionHandler:
    _cfg: SubscriptionHandlerConfig
    _sub_id_to_fltrs: dict[str, list[event_filter.EventFilter]]
    _response_queue: asyncio.Queue[str]
    _pending_deletes: set[str]
    _lock: asyncio.Lock

    def __init__(
        self,
        response_queue: asyncio.Queue[str],
        cfg: SubscriptionHandlerConfig = SubscriptionHandlerConfig(),
    ):
        self._cfg = cfg
        self._sub_id_to_fltrs = {}
        self._response_queue = response_queue
        self._pending_deletes = set()
        self._lock = asyncio.Lock()

    @locked()
    async def handle_event(self, ev: event.Event):
        for sub_id, fltrs in self._sub_id_to_fltrs.items():
            if fltrs and any(fltr.matches_event(ev) for fltr in fltrs):
                await self._response_queue.put(
                    relay_event.RelayEvent(sub_id, ev.__dict__).serialize()
                )

    @locked()
    async def set_filters(self, sub_id: str, fltrs: list[event_filter.EventFilter]):
        if sub_id in self._pending_deletes:
            self._pending_deletes.remove(sub_id)
        else:
            if len(sub_id) > self._cfg.max_subid_length:
                raise ConfigLimitsExceeded(
                    f"Subscription ID must be less than {self._cfg.max_subid_length} characters."
                )

            if len(self._sub_id_to_fltrs) >= self._cfg.max_subscriptions:
                raise ConfigLimitsExceeded(
                    f"Relay does not support more than {self._cfg.max_subscriptions} subscriptions."
                )

            self._sub_id_to_fltrs[sub_id] = fltrs

    @locked()
    async def clear_filters(self, sub_id: str):
        if sub_id not in self._sub_id_to_fltrs:
            self._pending_deletes.add(sub_id)
        else:
            del self._sub_id_to_fltrs[sub_id]
