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
import sys

import click
import websockets

from cli.read_cmd import metadata

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@click.group("cli")
@click.pass_context
@click.option("--relay-url")
@click.option("--ssl-no-verify", is_flag=True, default=False)
def cli(ctx: click.Context, relay_url: str, ssl_no_verify: bool):
    ctx.obj = {}
    ctx.obj["relay_url"] = relay_url
    ctx.obj["ssl_no_verify"] = ssl_no_verify


async def ping_websocket(ctx_obj):
    relay_url = ctx_obj["relay_url"]
    ws = await websockets.connect(relay_url)

    if ws.open:
        click.echo(f"Connection to {relay_url} succeeded.")
    else:
        click.echo(f"Failed connection to {relay_url} {ws.close_reason}")

    await ws.close()


@click.command()
@click.pass_obj
def ping(ctx_obj):
    relay_url = ctx_obj.relay_url
    asyncio.get_event_loop().run_until_complete(ping_websocket(relay_url))


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
