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
import dataclasses
import logging
import ssl
import sys

import click
import websockets
from websockets.client import connect

from cli.read_cmd import metadata

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@dataclasses.dataclass
class Context:
    relay_url: str
    event_loop: asyncio.AbstractEventLoop
    ws_conn: websockets.client.WebSocketClientProtocol

    def __del__(self):
        self.event_loop.run_until_complete(self.ws_conn.close())


@click.group("cli")
@click.pass_context
@click.option("--relay-url")
@click.option("--ssl-no-verify", is_flag=True, default=False)
def cli(ctx: click.Context, relay_url: str, ssl_no_verify: bool):
    ssl_context = None
    if "wss" in relay_url:
        ssl_context = ssl.create_default_context()
        if ssl_no_verify:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ctx.obj = Context(
        relay_url, loop, loop.run_until_complete(connect(relay_url, ssl=ssl_context))
    )


@click.command()
@click.pass_obj
def ping(ctx_obj):
    if ctx_obj.ws_conn.open:
        click.echo(f"Connection to {ctx_obj.relay_url} succeeded.")
    else:
        click.echo(
            f"Failed connection to {ctx_obj.relay_url} {ctx_obj.ws.close_reason}"
        )


@click.group
def read():
    pass


read.add_command(metadata.metadata)

cli.add_command(ping)
cli.add_command(read)


def main():
    cli(prog_name="cli")  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
