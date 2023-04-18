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
    auth_handler,
    event_handler,
    event_notifier,
    message_dispatcher,
    message_handler,
    subscription_handler,
)
from ndk.relay.event_repo import event_repo, memory_event_repo, mysql_event_repo
from ndk.repos.event_repo import protocol_handler
from relay import config

logger = logging.getLogger(__name__)

RELAY_EVENT_REPO = os.environ.get("RELAY_EVENT_REPO", "memory").lower()
HOST = os.environ.get("RELAY_HOST", "localhost")
PORT = int(os.environ.get("RELAY_PORT", "2700"))
DEBUG_LEVEL = os.environ.get("RELAY_LOG_LEVEL", "INFO")
RELAY_URL = os.environ.get("RELAY_URL", "wss://tests")

if RELAY_EVENT_REPO == "mysql":
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

logging.basicConfig(level=DEBUG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("websockets").setLevel(logging.WARNING)


async def process_message(
    data: str, write_queue: asyncio.Queue[str], md: message_dispatcher.MessageDispatcher
):
    try:
        responses = await md.process_message(data)
    except:  # pylint: disable=bare-except
        logger.exception("Error processing message: %s", data)
        return

    for response in responses:
        await write_queue.put(response)


async def connection_handler(
    read_queue: asyncio.Queue[str],
    write_queue: asyncio.Queue[str],
    md: message_dispatcher.MessageDispatcher,
):
    while True:
        data = await read_queue.get()
        read_queue.task_done()
        asyncio.create_task(process_message(data, write_queue, md))


async def handler_wrapper(
    cfg: config.RelayConfig, repo: event_repo.EventRepo, websocket
):
    logger.debug("New connection established from: %s", websocket.remote_address)
    request_queue: asyncio.Queue[str] = asyncio.Queue()
    response_queue: asyncio.Queue[str] = asyncio.Queue()

    auth = auth_handler.AuthHandler(RELAY_URL)
    sh = subscription_handler.SubscriptionHandler(
        response_queue,
        subscription_handler.SubscriptionHandlerConfig(
            cfg.limitations.max_subscriptions
        ),
    )
    ev_notifier = event_notifier.EventNotifier()
    eh = event_handler.EventHandler(
        repo,
        ev_notifier,
        event_handler.EventHandlerConfig(
            cfg.limitations.max_event_tags, cfg.limitations.max_content_length
        ),
    )
    mh = message_handler.MessageHandler(
        auth,
        repo,
        sh,
        eh,
        message_handler.MessageHandlerConfig(
            cfg.limitations.max_filters,
            cfg.limitations.max_limit,
            cfg.limitations.min_prefix,
        ),
    )
    md = message_dispatcher.MessageDispatcher(mh)
    eh.register_received_cb(sh.handle_event)
    await response_queue.put(auth.build_auth_message())

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


async def health_check(rid_bytes: bytes, path, headers):
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
            rid_bytes,
        )

    if "Upgrade" not in headers or headers["Upgrade"] != "websocket":
        return (http.HTTPStatus.NOT_FOUND, [], b"404 Not Found")


def parse_args():
    parser = argparse.ArgumentParser(description="Nostr Relay")
    parser.add_argument(
        "--config",
        help="path to the config file",
        type=str,
        required=False,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"),
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    ini_parser = configparser.ConfigParser()
    ini_parser.read(args.config)
    cfg = config.RelayConfig(ini_parser)

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
        functools.partial(handler_wrapper, cfg, repo),
        HOST,
        PORT,
        process_request=functools.partial(
            health_check, serialize.serialize_as_bytes(cfg.to_rid())
        ),
    ):
        await stop


if __name__ == "__main__":
    asyncio.run(main())
