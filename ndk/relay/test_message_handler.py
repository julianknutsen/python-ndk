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

import mock
import pytest

from ndk import exceptions
from ndk.event import auth_event, event, event_builder, event_filter
from ndk.messages import (
    auth,
    close,
    command_result,
    event_message,
    message_factory,
    request,
)
from ndk.relay import (
    event_handler,
    event_notifier,
    message_handler,
    subscription_handler,
)
from ndk.relay.event_repo import memory_event_repo


@pytest.fixture
def auth_hndlr():
    return mock.AsyncMock()


@pytest.fixture
def repo():
    return memory_event_repo.MemoryEventRepo()


@pytest.fixture
def sh_mock():
    return mock.Mock(wraps=subscription_handler.SubscriptionHandler(mock.MagicMock()))


@pytest.fixture
def eh_mock(repo):
    return mock.AsyncMock(
        wraps=event_handler.EventHandler(repo, notifier=event_notifier.EventNotifier())
    )


@pytest.fixture
def mh(auth_hndlr, repo, sh_mock, eh_mock):
    yield message_handler.MessageHandler(auth_hndlr, repo, sh_mock, eh_mock)


async def test_event_validation_failure_returns_command_result_false(mh):
    def raise_validation_error():
        raise exceptions.ValidationError("Failed validation")

    with mock.patch.object(
        event_builder, "from_dict", lambda self, **kwargs: raise_validation_error()
    ):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert not response_msg.accepted


async def test_accepted_returns_command_result_true(mh):
    mocked = mock.MagicMock()
    mocked.id = "1"

    with mock.patch.object(event_builder, "from_dict", lambda self, **kwargs: mocked):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert response_msg.accepted


async def test_accepted_calls_event_handler(mh, eh_mock):
    mocked = mock.MagicMock()
    mocked.id = "1"

    with mock.patch.object(event_builder, "from_dict", lambda self, **kwargs: mocked):
        await mh.handle_event_message(event_message.Event({"id": "1"}))

    eh_mock.handle_event.assert_called_with(mocked)


async def test_req_sets_filter(mh, sh_mock):
    await mh.handle_request(request.Request("sub", [{}]))

    sh_mock.set_filters.assert_called_once_with("sub", [event_filter.EventFilter()])


async def test_close_clears_filter(mh, sh_mock):
    await mh.handle_request(request.Request("sub", [{}]))
    await mh.handle_close(close.Close("sub"))

    sh_mock.clear_filters.assert_called_with("sub")


async def test_new_req_overwrites_filter(mh, sh_mock):
    await mh.handle_request(request.Request("sub", [{}]))
    await mh.handle_request(request.Request("sub", [{"ids": ["1"]}]))

    sh_mock.set_filters.assert_has_calls(
        [
            mock.call("sub", [event_filter.EventFilter()]),
            mock.call("sub", [event_filter.EventFilter(ids=["1"])]),
        ]
    )


async def test_accepted_calls_subscription_handler(mh, eh_mock, sh_mock):
    await eh_mock.register_received_cb(sh_mock.handle_event)
    mocked = mock.AsyncMock(spec=event.EphemeralEvent, id="1")
    with mock.patch.object(event_builder, "from_dict", lambda self, **kwargs: mocked):
        response = await mh.handle_event_message(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert response_msg.accepted
    sh_mock.handle_event.assert_called_with(mocked)


async def test_handle_auth_response(auth_hndlr, mh):
    ev = mock.Mock(auth_event.AuthEvent)
    msg = auth.AuthResponse(ev)
    await mh.handle_auth_response(msg)

    auth_hndlr.handle_auth_event.assert_called_once_with(ev)
