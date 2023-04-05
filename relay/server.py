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

import argparse
import asyncio
import configparser
import functools
import http
import logging
import os
import signal

from websockets.legacy.server import serve

from ndk import serialize
from ndk.relay import (
    event_handler,
    message_dispatcher,
    message_handler,
    relay_information_document,
    subscription_handler,
)
from ndk.relay.event_repo import event_repo, memory_event_repo, mysql_event_repo
from ndk.repos.event_repo import protocol_handler

logger = logging.getLogger(__name__)

RELAY_EVENT_REPO = os.environ.get("RELAY_EVENT_REPO", "memory").lower()
HOST = os.environ.get("RELAY_HOST", "localhost")
PORT = int(os.environ.get("RELAY_PORT", "2700"))
DEBUG_LEVEL = os.environ.get("RELAY_LOG_LEVEL", "INFO")

if RELAY_EVENT_REPO == "mysql":
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

logging.basicConfig(level=DEBUG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("websockets").setLevel(logging.WARNING)


async def connection_handler(
    read_queue: asyncio.Queue[str],
    write_queue: asyncio.Queue[str],
    md: message_dispatcher.MessageDispatcher,
):
    while True:
        data = await read_queue.get()
        read_queue.task_done()
        try:
            responses = await md.process_message(data)
        except:  # pylint: disable=bare-except
            logger.exception("Error processing message: %s", data)
            continue
        for response in responses:
            await write_queue.put(response)


async def handler_wrapper(repo: event_repo.EventRepo, websocket):
    logger.debug("New connection established from: %s", websocket.remote_address)
    request_queue: asyncio.Queue[str] = asyncio.Queue()
    response_queue: asyncio.Queue[str] = asyncio.Queue()

    sh = subscription_handler.SubscriptionHandler(response_queue)
    eh = event_handler.EventHandler(repo)
    mh = message_handler.MessageHandler(repo, sh, eh)
    md = message_dispatcher.MessageDispatcher(mh)
    repo.register_insert_cb(sh.handle_event)

    consumer_task = asyncio.create_task(
        protocol_handler.read_handler(websocket, request_queue)
    )
    producer_task = asyncio.create_task(
        protocol_handler.write_handler(websocket, response_queue)
    )
    processing_task = asyncio.create_task(
        connection_handler(request_queue, response_queue, md)
    )

    _, pending = await asyncio.wait(
        [consumer_task, producer_task, processing_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def health_check(
    rid: relay_information_document.RelayInformationDocument, path, headers
):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK"

    if (
        path == "/"
        and "Accept" in headers
        and headers["Accept"] == "application/nostr+json"
    ):
        return (
            http.HTTPStatus.OK,
            [
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Headers", "*"),
                ("Access-Control-Allow-Methods", "GET"),
            ],
            rid.serialize_as_bytes(),
        )

    if "Upgrade" not in headers or headers["Upgrade"] != "websocket":
        return (http.HTTPStatus.NOT_FOUND, [], b"404 Not Found")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate load on a relay")
    parser.add_argument(
        "--config",
        help="path to the config file",
        type=str,
        required=False,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"),
    )
    return parser.parse_args()


def parse_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def build_rid(config):
    return relay_information_document.RelayInformationDocument(
        name=config.get("General", "name"),
        description=config.get("General", "description"),
        software=config.get("General", "software"),
        supported_nips=serialize.deserialize(config.get("General", "supported_nips")),
        version=config.get("General", "version"),
        limitation_auth_required=config.getboolean("Limitation", "auth_required"),
        limitation_payment_required=config.getboolean("Limitation", "payment_required"),
    )


async def main():
    args = parse_args()
    config = parse_config(args.config)

    logger.info("Logging set to %s", DEBUG_LEVEL)

    if RELAY_EVENT_REPO == "memory":
        repo = memory_event_repo.MemoryEventRepo()
    elif RELAY_EVENT_REPO == "mysql":
        repo = await mysql_event_repo.MySqlEventRepo.create(
            DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
        )
    else:
        raise ValueError(f"Unknown event repo: {RELAY_EVENT_REPO}")
    logger.info("%s initialized", repo.__class__)

    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with serve(
        functools.partial(handler_wrapper, repo),
        HOST,
        PORT,
        process_request=functools.partial(health_check, build_rid(config)),
    ):
        await stop


if __name__ == "__main__":
    asyncio.run(main())
