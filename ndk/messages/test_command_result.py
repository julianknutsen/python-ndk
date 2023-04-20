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

import pytest

from ndk import serialize
from ndk.messages import command_result, message_factory


def test_input_non_list():
    msg = {}

    with pytest.raises(AssertionError):
        command_result.CommandResult.deserialize_list(msg)  # type: ignore


def test_ok_bad_len():
    msg = ["OK"]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_ok_wrong_type_event_id():
    msg = ["OK", 1, True, "message"]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_ok_wrong_type_accepted():
    msg = ["OK", "eventid", "True", "message"]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_ok_wrong_type_message():
    msg = ["OK", "eventid", True, False]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_correct_not_accepted_empty_message():
    msg = ["OK", "eventid", False, ""]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_correct_accepted_empty_message_works():
    msg = ["OK", "eventid", True, ""]

    command_result.CommandResult.deserialize_list(msg)


def test_ok_correct_accepted():
    msg = ["OK", "eventid", True, "message"]

    cr = command_result.CommandResult.deserialize_list(msg)

    assert cr.is_success()


def test_ok_correct_not_accepted_empty_message_fails():
    msg = ["OK", "eventid", False, ""]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_ok_correct_not_accepted():
    msg = ["OK", "eventid", False, "message"]

    cr = command_result.CommandResult.deserialize_list(msg)

    assert not cr.is_success()


@pytest.mark.parametrize("msg", command_result.REJECTED_MSG_PREFIXES)
def test_rejected_messages_match_accepted_status(msg):
    msg = ["OK", "eventid", True, msg]

    with pytest.raises(TypeError):
        command_result.CommandResult.deserialize_list(msg)


def test_serialize():
    cr = command_result.CommandResult("1", True, "msg")

    assert serialize.deserialize_str(cr.serialize()) == ["OK", "1", True, "msg"]


def test_factory_correct():
    msg = ["OK", "eventid", False, "message"]
    cr = message_factory.from_str(serialize.serialize_as_str(msg))
    assert isinstance(cr, command_result.CommandResult)
