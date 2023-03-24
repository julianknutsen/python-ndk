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

from ndk.event import event
from ndk.messages import command_result, event_message, message_factory
from relay import event_repo, message_handler


@pytest.fixture
def eh():
    repo = event_repo.EventRepo()
    yield message_handler.MessageHandler(repo)


def test_event_validation_failure(eh):
    def raise_validation_error():
        raise event.ValidationError("Failed validation")

    with mock.patch.object(
        event.SignedEvent, "from_dict", lambda self, **kwargs: raise_validation_error()
    ):
        response = eh.handle_event(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert not response_msg.accepted


def test_accepted_event(eh):
    mocked = mock.MagicMock()
    mocked.id = "1"

    with mock.patch.object(
        event.SignedEvent, "from_dict", lambda self, **kwargs: mocked
    ):
        response = eh.handle_event(event_message.Event({"id": "1"}))

        assert len(response) == 1
        response_msg = message_factory.from_str(response[0])

        assert isinstance(response_msg, command_result.CommandResult)
        assert response_msg.accepted
