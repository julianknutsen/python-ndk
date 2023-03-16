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

import pprint

import click
import websocket

from ndk.repos.event_repo import relay_event_repo
from ndk.repos.metadata_repo import event_backed_metadata_repo


class RelayEventRW(relay_event_repo.RelayEventRepo):
    _ws: websocket.WebSocket

    def __init__(self, url: str):
        ws = websocket.WebSocket()
        ws.connect(url)
        if not ws.connect:
            click.get_current_context().fail(f"Cant connect to relay: {url}")

        super().__init__(ws.send, ws.recv)
        self._ws = ws

    def __del__(self):
        self._ws.close()


@click.command()
@click.pass_obj
@click.argument("pubkey")
def metadata(relay_url, pubkey):
    ev_repo = RelayEventRW(relay_url)
    repo = event_backed_metadata_repo.EventBackedMetadataRepo(ev_repo)

    click.echo(pprint.pformat(repo.get(pubkey), width=80))
