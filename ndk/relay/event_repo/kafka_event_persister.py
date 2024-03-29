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
import logging

import aiokafka

from ndk.relay.event_repo import event_repo, kafka_events

logger = logging.getLogger(__name__)

WORKER_COUNT = 8


class KafkaEventPersister:
    _consumer: aiokafka.AIOKafkaConsumer
    _event_repo: event_repo.EventRepo
    _topic: str

    def __init__(self, kafka_url: str, topic: str, ev_repo: event_repo.EventRepo):
        self._consumer = aiokafka.AIOKafkaConsumer(
            topic,
            bootstrap_servers=kafka_url,
            group_id="event_persister",
        )
        self._event_repo = ev_repo
        self._topic = topic

    async def start_worker(self, work_queue):
        while True:
            kafka_event = kafka_events.KafkaEvent.deserialize(await work_queue.get())

            logger.debug("Handling %s", kafka_event)
            if isinstance(kafka_event, kafka_events.CreatOrUpdateEvent):
                try:
                    await self._event_repo.add(kafka_event.ev)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Failed to add event %s", kafka_event.ev, exc_info=exc)
            else:
                raise ValueError(f"Unknown kafka event type: {kafka_event}")

    async def start(self):
        await self._consumer.start()
        logger.debug("Started consumer for topic %s", self._topic)
        work_queue = asyncio.Queue(maxsize=WORKER_COUNT)
        workers = [
            asyncio.create_task(self.start_worker(work_queue))
            for _ in range(WORKER_COUNT)
        ]
        async for message in self._consumer:
            await work_queue.put(message.value)

        for t in workers:
            t.cancel()
        await self._consumer.stop()
