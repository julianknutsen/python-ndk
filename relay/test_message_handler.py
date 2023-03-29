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

import mock
import pytest

from ndk.event import event, event_filter
from ndk.messages import close, command_result, event_message, message_factory, request
from relay import message_handler, subscription_handler
from relay.event_repo import memory_event_repo


@pytest.fixture
def mh():
    sh = subscription_handler.SubscriptionHandler(asyncio.Queue())
    repo = memory_event_repo.MemoryEventRepo()
    repo.register_insert_cb(sh.handle_event)
    yield message_handler.MessageHandler(repo, sh)


async def test_event_validation_failure(mh):
    def raise_validation_error():
        raise event.ValidationError("Failed validation")

    with mock.patch.object(
        event.SignedEvent, "from_dict", lambda self, **kwargs: raise_validation_error()
    ):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert not response_msg.accepted


async def test_accepted_event(mh):
    mocked = mock.MagicMock()
    mocked.id = "1"

    with mock.patch.object(
        event.SignedEvent, "from_dict", lambda self, **kwargs: mocked
    ):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert response_msg.accepted


async def test_req_sets_filter():
    repo = memory_event_repo.MemoryEventRepo()
    sh = mock.MagicMock()
    mh = message_handler.MessageHandler(repo, sh)
    await mh.handle_request(request.Request("sub", [{}]))

    sh.set_filters.assert_called_once_with("sub", [event_filter.EventFilter()])


async def test_close_clears_filter():
    repo = memory_event_repo.MemoryEventRepo()
    sh = mock.MagicMock()
    mh = message_handler.MessageHandler(repo, sh)
    await mh.handle_request(request.Request("sub", [{}]))
    await mh.handle_close(close.Close("sub"))

    sh.clear_filters.assert_called_with("sub")


async def test_new_req_overwrites_filter():
    repo = memory_event_repo.MemoryEventRepo()
    sh = mock.MagicMock()
    mh = message_handler.MessageHandler(repo, sh)
    repo.register_insert_cb(sh.handle_event)

    await mh.handle_request(request.Request("sub", [{}]))
    await mh.handle_request(request.Request("sub", [{"ids": ["1"]}]))

    sh.set_filters.assert_has_calls(
        [
            mock.call("sub", [event_filter.EventFilter()]),
            mock.call("sub", [event_filter.EventFilter(ids=["1"])]),
        ]
    )


async def test_accepted_calls_subscription_handler():
    repo = memory_event_repo.MemoryEventRepo()
    sh = mock.AsyncMock()
    mh = message_handler.MessageHandler(repo, sh)
    repo.register_insert_cb(sh.handle_event)

    mocked = mock.AsyncMock()
    mocked.id = "1"
    with mock.patch.object(
        event.SignedEvent, "from_dict", lambda self, **kwargs: mocked
    ):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert response_msg.accepted
    sh.handle_event.assert_called_with(mocked)
