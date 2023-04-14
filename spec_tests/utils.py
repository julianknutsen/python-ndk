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

# pylint: disable=redefined-outer-name, unused-argument

import typing

from ndk.event import (
    event,
    event_builder,
    reaction_event,
    repost_event,
    text_note_event,
)
from ndk.messages import (
    close,
    command_result,
    eose,
    event_message,
    message_factory,
    relay_event,
    request,
)


async def send_and_expect_command_result(
    signed_event: event.SignedEvent, request_queue, response_queue
) -> command_result.CommandResult:
    await request_queue.put(
        event_message.Event.from_signed_event(signed_event).serialize()
    )
    return await expect_successful_command_result(response_queue)


async def send_req_with_filter(sub_id, fltrs, request_queue):
    r = request.Request(sub_id, fltrs)
    await request_queue.put(r.serialize())


async def send_close(sub_id, request_queue):
    r = close.Close(sub_id)
    await request_queue.put(r.serialize())


async def expect_relay_event(response_queue):
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, relay_event.RelayEvent)
    return msg


async def expect_successful_command_result(response_queue):
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, command_result.CommandResult)
    assert msg.accepted
    return msg


async def expect_relay_event_of_type(
    event_type: typing.Type[event.SignedEvent], response_queue
):
    msg = await expect_relay_event(response_queue)
    signed = event_builder.from_dict(msg.event_dict)
    assert isinstance(signed, event_type)
    return signed


async def expect_text_note_event(response_queue) -> event.SignedEvent:
    return await expect_relay_event_of_type(
        text_note_event.TextNoteEvent, response_queue
    )


async def expect_repost_event(response_queue) -> event.SignedEvent:
    return await expect_relay_event_of_type(repost_event.RepostEvent, response_queue)


async def expect_reaction_event(response_queue) -> event.SignedEvent:
    return await expect_relay_event_of_type(
        reaction_event.ReactionEvent, response_queue
    )


async def expect_eose(response_queue):
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, eose.EndOfStoredEvents)
