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

import logging

from ndk import exceptions
from ndk.event import event
from ndk.messages import command_result, event_message, message, message_factory, notice

logger = logging.getLogger(__name__)


def create_notice(text: str) -> str:
    return notice.Notice(text).serialize()


def create_cmd_result(ev_id: str, accepted: bool, msg: str):
    return command_result.CommandResult(ev_id, accepted, msg).serialize()


class MessageHandler:
    def process_message(self, data: str) -> str:
        try:
            msg = message_factory.from_str(data)
            return self._handle_msg(msg)
        except exceptions.ParseError:
            text = f"Unable to parse message: {data}"
            logger.debug(text, exc_info=True)
            return create_notice(text)

    def _handle_msg(self, msg: message.Message) -> str:
        if isinstance(msg, event_message.Event):
            return self._handle_event(msg)
        else:
            return create_notice(f"Server does not support message of type: {msg}")

    def _handle_event(self, msg: event_message.Event) -> str:
        try:
            signed_ev = event.SignedEvent.from_dict(msg.event_dict)
            return create_cmd_result(signed_ev.id, True, "")
        except event.ValidationError:
            text = f"Event validation failed: {msg}"
            logger.debug(text, exc_info=True)
            ev_id = msg.event_dict["id"]  # guaranteed if passed Type check above
            return create_cmd_result(ev_id, False, text)
