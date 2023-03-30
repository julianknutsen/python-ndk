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
import pprint
import ssl
import traceback

import click
from websockets.client import connect
from websockets.legacy.client import WebSocketClientProtocol

from ndk.repos.event_repo import protocol_handler, relay_event_repo
from ndk.repos.metadata_repo import event_backed_metadata_repo

logger = logging.getLogger(__name__)


async def _start_websocket(relay_url: str, ssl_no_verify: bool):
    ssl_context = None
    if "wss" in relay_url:
        ssl_context = ssl.create_default_context()
        if ssl_no_verify:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

    return await connect(relay_url, ssl=ssl_context)


class ProtocolContext:
    protocol: protocol_handler.ProtocolHandler
    _relay_url: str
    _verify_ssl: bool
    _rq: asyncio.Queue
    _wq: asyncio.Queue
    _ws: WebSocketClientProtocol
    _tasks: list

    def __init__(self, relay_url: str, verify_ssl: bool):
        self._relay_url = relay_url
        self._verify_ssl = verify_ssl

    def __enter__(self):
        logger.debug("__aenter__")
        self._rq = asyncio.Queue()
        self._wq = asyncio.Queue()
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ws = self._loop.run_until_complete(
            _start_websocket(self._relay_url, self._verify_ssl)
        )

        reader_task = self._loop.create_task(
            protocol_handler.read_handler(self._ws, self._rq)
        )
        writer_task = self._loop.create_task(
            protocol_handler.write_handler(self._ws, self._wq)
        )

        self.protocol = protocol_handler.ProtocolHandler(self._rq, self._wq)
        protocol_read_loop = self._loop.create_task(self.protocol.start_read_loop())

        self._tasks = [reader_task, writer_task, protocol_read_loop]

        return self

    def __exit__(self, exc_type, exc_val, tb):
        logger.debug("__aexit__")
        if exc_val:
            logger.error(
                "Exception: [%s] %s %s", exc_type, exc_val, traceback.format_tb(tb)
            )

        self._loop.run_until_complete(self.protocol.stop_read_thread())
        for task in self._tasks:
            task.cancel()
        self._loop.run_until_complete(self._ws.close())


@click.command()
@click.pass_obj
@click.argument("pubkey")
def metadata(ctx_obj, pubkey):
    with ProtocolContext(ctx_obj["relay_url"], ctx_obj["ssl_no_verify"]) as pc:
        ev_repo = relay_event_repo.RelayEventRepo(pc.protocol)
        repo = event_backed_metadata_repo.EventBackedMetadataRepo(ev_repo)

        response = asyncio.get_event_loop().run_until_complete(repo.get(pubkey))

        click.echo(pprint.pformat(response, width=80))
