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
import os

from ndk.relay.event_repo import kafka_event_persister, postgres_event_repo

logger = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG", format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("aiokafka").setLevel(logging.INFO)

KAFKA_URL = os.environ.get("KAFKA_URL", "")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")


async def main():
    repo = await postgres_event_repo.PostgresEventRepo.create(
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    )
    persister = kafka_event_persister.KafkaEventPersister(KAFKA_URL, "events", repo)
    await persister.start()


if __name__ == "__main__":
    asyncio.run(main())
