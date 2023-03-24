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

import pytest

from ndk import serialize
from ndk.messages import close, eose, event_message, message_factory, notice, request
from relay import event_repo, message_dispatcher, message_handler


@pytest.fixture
def md():
    repo = event_repo.EventRepo()
    ev_handler = message_handler.MessageHandler(repo)
    return message_dispatcher.MessageDispatcher(ev_handler)


def test_init(md):  # pylint: disable=unused-argument
    # done in fixture
    pass


def test_process_invalid_obj(md):
    response = md.process_message(serialize.serialize_as_str({}))

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


def test_process_invalid_list(md):
    response = md.process_message(serialize.serialize_as_str([]))

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


def test_process_unsupported_ev(md):
    req = notice.Notice("huh?")
    response = md.process_message(req.serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


def test_event_missing_required_fields(md):
    response = md.process_message(event_message.Event({}).serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, notice.Notice)


def test_close_does_nothing(md):
    response = md.process_message(close.Close("1").serialize())

    assert len(response) == 0


def test_handle_request_no_match(md):
    response = md.process_message(request.Request("1", [{}]).serialize())

    assert len(response) == 1
    response_msg = message_factory.from_str(response[0])

    assert isinstance(response_msg, eose.EndOfStoredEvents)
