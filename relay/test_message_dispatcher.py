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
# pylint: disable=redefined-outer-name

import asyncio

import pytest

from ndk import serialize
from ndk.messages import close, eose, event_message, message_factory, notice, request
from relay import (
    event_handler,
    message_dispatcher,
    message_handler,
    subscription_handler,
)
from relay.event_repo import memory_event_repo


@pytest.fixture
def md():
    sh = subscription_handler.SubscriptionHandler(asyncio.Queue())
    repo = memory_event_repo.MemoryEventRepo()
    eh = event_handler.EventHandler(repo)
    ev_handler = message_handler.MessageHandler(repo, sh, eh)
    return message_dispatcher.MessageDispatcher(ev_handler)


async def test_init(md):  # pylint: disable=unused-argument
    # done in fixture
    pass


async def test_process_invalid_obj(md):
    response = await md.process_message(serialize.serialize_as_str({}))

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


async def test_process_invalid_list(md):
    response = await md.process_message(serialize.serialize_as_str([]))

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


async def test_process_unsupported_ev(md):
    req = notice.Notice("huh?")
    response = await md.process_message(req.serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


async def test_event_missing_required_fields(md):
    response = await md.process_message(event_message.Event({}).serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


async def test_close_without_req_raises(md):
    with pytest.raises(ValueError):
        await md.process_message(close.Close("1").serialize())


async def test_handle_request_no_match(md):
    response = await md.process_message(request.Request("1", [{}]).serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, eose.EndOfStoredEvents)
