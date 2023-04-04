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
from ndk.messages import close, event_message, message, message_factory, notice, request
from ndk.relay import message_handler

logger = logging.getLogger(__name__)


def create_notice(text: str) -> str:
    return notice.Notice(text).serialize()


class MessageDispatcher:
    def __init__(self, ev_handler: message_handler.MessageHandler):
        self._ev_handler = ev_handler

    async def process_message(self, data: str) -> list[str]:
        try:
            msg = message_factory.from_str(data)
            return await self._handle_msg(msg)
        except exceptions.ParseError:
            text = f"Unable to parse message: {data}"
            logger.debug(text, exc_info=True)
            return [create_notice(text)]

    async def _handle_msg(self, msg: message.Message) -> list[str]:
        if isinstance(msg, event_message.Event):
            return await self._ev_handler.handle_event_message(msg)
        elif isinstance(msg, request.Request):
            return await self._ev_handler.handle_request(msg)
        elif isinstance(msg, close.Close):
            return await self._ev_handler.handle_close(msg)
        else:
            return [create_notice(f"Relay does not support message of type: {msg}")]