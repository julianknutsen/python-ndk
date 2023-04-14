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

from ndk.event import event, event_filter
from ndk.messages import relay_event


class SubscriptionHandler:
    _sub_id_to_fltrs: dict[str, list[event_filter.EventFilter]]
    _response_queue: asyncio.Queue[str]

    def __init__(self, response_queue: asyncio.Queue[str]):
        self._sub_id_to_fltrs = {}
        self._response_queue = response_queue

    async def handle_event(self, ev: event.Event):
        for sub_id, fltrs in self._sub_id_to_fltrs.items():
            if fltrs and any(fltr.matches_event(ev) for fltr in fltrs):
                await self._response_queue.put(
                    relay_event.RelayEvent(sub_id, ev.__dict__).serialize()
                )

    def set_filters(self, sub_id: str, fltrs: list[event_filter.EventFilter]):
        self._sub_id_to_fltrs[sub_id] = fltrs

    def clear_filters(self, sub_id: str):
        if sub_id not in self._sub_id_to_fltrs:
            raise ValueError(f"Subscription {sub_id} does not exist")
        del self._sub_id_to_fltrs[sub_id]
