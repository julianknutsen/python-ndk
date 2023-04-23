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

import aiokafka

from ndk import types
from ndk.event import event, event_filter
from ndk.relay.event_repo import event_repo, kafka_events


class KafkaEventRepo(event_repo.EventRepo):
    _producer: aiokafka.AIOKafkaProducer
    _repo: event_repo.EventRepo
    _started: bool
    _topic: str

    def __init__(
        self,
        kafka_url: str,
        repo: event_repo.EventRepo,
        topic: str,
    ):
        self._producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=kafka_url,
            loop=asyncio.get_event_loop(),
            value_serializer=lambda v: v.serialize(),
            compression_type="gzip",
        )
        self._repo = repo
        self._started = False
        self._topic = topic
        super().__init__()

    def __del__(self):
        asyncio.run(self._producer.stop())

    async def start(self):
        await self._producer.start()
        self._started = True

    async def _delete_old_events(self, ev: event.Event):
        pass  # handled by the kafka consumer

    async def _persist(self, ev: event.Event) -> types.EventID:
        assert self._started
        kafka_event = kafka_events.CreatOrUpdateEvent.create(ev)
        await self._producer.send_and_wait(self._topic, kafka_event)

        return ev.id

    async def get(self, fltrs: list[event_filter.EventFilter]) -> list[event.Event]:
        return await self._repo.get(fltrs)

    async def remove(self, event_id: types.EventID):
        await self._repo.remove(event_id)
