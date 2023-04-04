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

from ndk import crypto
from ndk.event import event, metadata_event
from ndk.relay import (
    event_handler,
    message_dispatcher,
    message_handler,
    subscription_handler,
)
from ndk.relay.event_repo import memory_event_repo
from ndk.repos.event_repo import protocol_handler, relay_event_repo
from relay import server


async def test_init():
    rq = asyncio.Queue()
    wq = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(wq)
    repo = memory_event_repo.MemoryEventRepo()
    eh = event_handler.EventHandler(repo)
    mh = message_handler.MessageHandler(repo, sh, eh)
    mb = message_dispatcher.MessageDispatcher(mh)
    handler_task = asyncio.create_task(server.connection_handler(rq, wq, mb))

    keys = crypto.KeyPair()
    ev = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(ev, keys)

    ph = protocol_handler.ProtocolHandler(wq, rq)
    read_loop_task = asyncio.create_task(ph.start_read_loop())
    ev_repo = relay_event_repo.RelayEventRepo(ph)

    ev_id = await ev_repo.add(signed)
    assert ev_id == signed.id

    await rq.join()
    await wq.join()

    await ph.stop_read_thread()
    await read_loop_task

    handler_task.cancel()
    try:
        await handler_task
    except asyncio.CancelledError:
        pass
