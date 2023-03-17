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

import json

import pytest

from ndk.event import command_result


def test_input_non_list():
    msg = {}

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_input_notice_message():
    msg = ["NOTICE", "uh oh"]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_not_ok_not_notice():
    msg = ["EVENT"]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_bad_len():
    msg = ["OK"]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_wrong_type_event_id():
    msg = ["OK", 1, True, "message"]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_wrong_type_accepted():
    msg = ["OK", "eventid", "True", "message"]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_wrong_type_message():
    msg = ["OK", "eventid", True, False]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_correct_empty_message():
    msg = ["OK", "eventid", True, ""]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))


def test_ok_correct_accepted():
    msg = ["OK", "eventid", True, "message"]

    cr = command_result.CommandResult.deserialize(json.dumps(msg))

    assert cr.is_success()


def test_ok_correct_not_accepted():
    msg = ["OK", "eventid", False, "message"]

    cr = command_result.CommandResult.deserialize(json.dumps(msg))

    assert not cr.is_success()


@pytest.mark.parametrize("msg", command_result.REJECTED_MSG_PREFIXES)
def test_rejected_messages_match_accepted_status(msg):
    msg = ["OK", "eventid", True, msg]

    with pytest.raises(ValueError):
        command_result.CommandResult.deserialize(json.dumps(msg))
