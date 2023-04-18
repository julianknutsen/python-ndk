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

from ndk import exceptions
from ndk.event import event, event_filter
from ndk.event import parameterized_replaceable_event as pre
from ndk.relay import event_notifier
from ndk.relay.event_repo import event_repo


@dataclasses.dataclass
class EventHandlerConfig:
    max_event_tags: int = 100
    max_content_length: int = 8196


class EventHandler:
    _received_event_notifier: event_notifier.EventNotifier
    _repo: event_repo.EventRepo
    _config = EventHandlerConfig

    def __init__(
        self,
        repo: event_repo.EventRepo,
        notifier: event_notifier.EventNotifier,
        cfg: EventHandlerConfig = EventHandlerConfig(),
    ):
        self._received_event_notifier = notifier
        self._repo = repo
        self._cfg = cfg

    async def handle_event(self, ev: event.Event):
        if ev.content is not None and len(ev.content) > self._cfg.max_content_length:
            raise exceptions.ValidationError(
                f"Relay doesn't support content greater than {self._cfg.max_content_length} bytes"
            )

        if len(ev.tags) > self._cfg.max_event_tags:
            raise exceptions.ValidationError(
                f"Relay doesn't support more than {self._cfg.max_event_tags} tags"
            )

        if isinstance(ev, event.PersistentEvent):
            await self._repo.add(ev)

        if isinstance(ev, event.SingletonEvent):
            if isinstance(ev, event.ReplaceableEvent):
                existing_evs = await self._repo.get(
                    [event_filter.EventFilter(authors=[ev.pubkey], kinds=[ev.kind])]
                )

            else:
                assert isinstance(ev, pre.ParameterizedReplaceableEvent)
                fltrs = []
                existing_evs = []
                normalized_d_tag = ev.get_normalized_d_tag_value()
                if normalized_d_tag is None:
                    # search for ["d", ""], or no tag at all, per NIP-33
                    fltrs.append(
                        event_filter.EventFilter(authors=[ev.pubkey], kinds=[ev.kind])
                    )

                    # query language has no way to search for "no tag" so need to check them all
                    existing_evs = await self._repo.get(fltrs)
                    existing_evs = [
                        ev
                        for ev in existing_evs
                        if len(ev.tags) == 0
                        or (ev.tags[0][0] == "d" and ev.tags[0][1] == "")
                    ]
                else:
                    fltrs.append(
                        event_filter.EventFilter(
                            authors=[ev.pubkey],
                            kinds=[ev.kind],
                            generic_tags={"d": [normalized_d_tag]},
                        )
                    )

                    existing_evs = await self._repo.get(fltrs)

            for e in existing_evs[1:]:  # first entry (latest) is the one we just added
                await self._repo.remove(e.id)

        if isinstance(ev, event.BroadcastEvent):
            await self._received_event_notifier.handle_event(ev)

    def register_received_cb(
        self, cb: event_notifier.EventNotifierCb
    ) -> event_notifier.EventNotifierCbId:
        return self._received_event_notifier.register(cb)

    def unregister_received_cb(self, cb_id: event_notifier.EventNotifierCbId):
        self._received_event_notifier.unregister(cb_id)
