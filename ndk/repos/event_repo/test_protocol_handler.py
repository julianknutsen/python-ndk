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
from ndk.event import event_filter, metadata_event
from ndk.messages import command_result, event_message
from ndk.repos.event_repo import protocol_handler


@pytest.fixture
async def read_queue() -> asyncio.Queue:
    return asyncio.Queue()


@pytest.fixture
async def write_queue() -> asyncio.Queue:
    return asyncio.Queue()


@pytest.fixture(autouse=True)
async def local_protocol(keys, read_queue: asyncio.Queue, write_queue: asyncio.Queue):
    t = protocol_handler.ProtocolHandler(keys, "wss://tests", read_queue, write_queue)
    read_task = asyncio.create_task(t.start_read_loop())
    await asyncio.sleep(0)
    yield t
    await t.stop_read_thread()
    await read_task


@pytest.fixture()
async def event(keys):
    return metadata_event.MetadataEvent.from_metadata_parts(keys)


async def test_init_reader():
    pass  # init done in fixture


async def simulate_server_reponse(read_queue, data: list):
    await read_queue.put(serialize.serialize_as_str(data))
    await read_queue.join()


async def test_read_notice(read_queue, caplog):
    await simulate_server_reponse(read_queue, ["NOTICE", "Uh oh!"])

    assert "Uh oh!" in caplog.text


async def assert_sent(write_queue, expected: str):
    data = await write_queue.get()
    write_queue.task_done()
    assert expected == data


async def test_write_event(read_queue, write_queue, local_protocol, event):
    future_cmd_result = asyncio.create_task(local_protocol.write_event(event))

    await assert_sent(write_queue, event_message.Event.from_event(event).serialize())

    await simulate_server_reponse(read_queue, ["OK", event.id, True, ""])

    assert await future_cmd_result == command_result.CommandResult(event.id, True, "")


async def test_write_event_receive_bad_data_logs(
    read_queue, local_protocol, caplog, event
):
    future_cmd_result = asyncio.create_task(local_protocol.write_event(event))

    await simulate_server_reponse(read_queue, [])

    assert not future_cmd_result.done()
    future_cmd_result.cancel()
    await read_queue.join()

    assert "Error parsing from read queue" in caplog.text


async def test_event_received_before_query(read_queue, caplog):
    await simulate_server_reponse(read_queue, ["EVENT", "unknown-sub-id", {}])

    assert "Dropping received message" in caplog.text


async def test_query_sends_correct_message(write_queue, local_protocol):
    future_events = asyncio.create_task(
        local_protocol.query_events([event_filter.EventFilter(kinds=[0])])
    )

    # verify correct message was sent to server
    data = await write_queue.get()
    write_queue.task_done()
    request = serialize.deserialize(data)
    assert isinstance(request, list)
    assert request[0] == "REQ"

    assert not future_events.done()
    future_events.cancel()


async def test_query_success_empty(read_queue, write_queue, local_protocol):
    future_events = asyncio.create_task(
        local_protocol.query_events([event_filter.EventFilter(kinds=[0])])
    )

    data = await write_queue.get()
    write_queue.task_done()
    request = serialize.deserialize(data)

    await simulate_server_reponse(read_queue, ["EOSE", request[1]])

    events = await future_events

    assert len(events) == 0


async def test_query_success(read_queue, write_queue, local_protocol, event):
    future_events = asyncio.create_task(
        local_protocol.query_events([event_filter.EventFilter(kinds=[0])])
    )

    data = await write_queue.get()
    write_queue.task_done()
    request = serialize.deserialize(data)

    await read_queue.put(
        serialize.serialize_as_str(["EVENT", request[1], event.__dict__])
    )

    await read_queue.put(serialize.serialize_as_str(["EOSE", request[1]]))

    events = await future_events

    assert len(events) == 1
    assert events[0] == event


async def test_auth_challenge(read_queue, write_queue):
    await simulate_server_reponse(read_queue, ["AUTH", "challenge"])

    # verify correct message was sent to server
    data = await write_queue.get()
    write_queue.task_done()
    request = serialize.deserialize(data)
    assert isinstance(request, list)
    assert request[0] == "AUTH"
