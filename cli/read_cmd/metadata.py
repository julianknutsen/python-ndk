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
import traceback

import click
import websockets

from ndk.repos.event_repo import protocol_handler, relay_event_repo
from ndk.repos.metadata_repo import event_backed_metadata_repo

logger = logging.getLogger(__name__)


class ProtocolContext:
    _loop: asyncio.AbstractEventLoop
    protocol: protocol_handler.ProtocolHandler
    _rq: asyncio.Queue
    _wq: asyncio.Queue
    _ws: websockets.client.WebSocketClientProtocol
    _tasks: list

    def __init__(
        self,
        conn: websockets.client.WebSocketClientProtocol,
        loop: asyncio.AbstractEventLoop,
    ):
        self._ws = conn
        self._loop = loop

    def __enter__(self):
        logger.debug("__aenter__")
        self._rq = asyncio.Queue()
        self._wq = asyncio.Queue()

        reader_task = self._loop.create_task(
            protocol_handler.read_handler(self._ws, self._rq)
        )
        writer_task = self._loop.create_task(
            protocol_handler.write_handler(self._ws, self._wq)
        )

        self.protocol = protocol_handler.ProtocolHandler(None, None, self._rq, self._wq)
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


@click.command()
@click.pass_obj
@click.argument("pubkey")
def metadata(ctx_obj, pubkey):
    with ProtocolContext(ctx_obj.ws_conn, ctx_obj.event_loop) as pc:
        ev_repo = relay_event_repo.RelayEventRepo(pc.protocol)
        repo = event_backed_metadata_repo.EventBackedMetadataRepo(ev_repo)

        response = asyncio.get_event_loop().run_until_complete(repo.get(pubkey))

        click.echo(pprint.pformat(response, width=80))
