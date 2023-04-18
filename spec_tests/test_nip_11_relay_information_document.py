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

import warnings

import pytest
import requests

from ndk import serialize
from ndk.event import event, event_tags
from ndk.messages import command_result, event_message, message_factory, notice, request


@pytest.fixture
def relay_info(relay_url, remote_relay):
    url = relay_url.replace("wss://", "https://")
    response = requests.get(
        url, headers={"Accept": "application/nostr+json"}, timeout=10, verify=False
    )

    if response.status_code != 200:
        warnings.warn(f"No support for NIP11, got {response.status_code} from {url}")
        pytest.skip()
    else:
        return serialize.deserialize(response.content.decode())


def skip_if_no_field(relay_info, category, field):
    if category not in relay_info or field not in relay_info[category]:
        text = f"No {category}.{field} in relay_info"
        warnings.warn(text)
        pytest.skip(text)


def test_basic(relay_info):
    pass  # test in fixture


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "description",
        "pubkey",
        "contact",
        "supported_nips",
        "software",
        "version",
        "foobar",
    ],
)
def test_has_known_general_fields(field, relay_info):
    if field not in relay_info:
        warnings.warn(f"No '{field}' field in response")


@pytest.mark.parametrize(
    "field",
    [
        "max_message_length",
        "max_subscriptions",
        "max_filters",
        "max_limit",
        "max_subid_length",
        "min_prefix",
        "max_event_tags",
        "max_content_length",
        "min_pow_difficulty",
        "auth_required",
        "payment_required",
    ],
)
def test_has_known_limitation_fields(field, relay_info):
    skip_if_no_field(relay_info, "limitation", field)


async def test_event_over_configured_size_errors(
    relay_info, keys, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "max_content_length")

    max_supported_size = relay_info["limitation"]["max_content_length"]
    ev = event.RegularEvent.build(
        keys, kind=1000, content="a" * (max_supported_size + 1)
    )

    await request_queue.put(event_message.Event.from_event(ev).serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, command_result.CommandResult)
    assert not msg.accepted


async def test_event_over_configured_tags_errors(
    relay_info, keys, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "max_event_tags")

    max_supported_size = relay_info["limitation"]["max_event_tags"]
    ev = event.RegularEvent.build(
        keys,
        kind=1000,
        tags=event_tags.EventTags([["d", ""] for _ in range(max_supported_size + 1)]),
    )

    await request_queue.put(event_message.Event.from_event(ev).serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, command_result.CommandResult)
    assert not msg.accepted


async def test_message_over_configured_length_errors(
    relay_info, keys, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "max_message_length")

    max_supported_size = relay_info["limitation"]["max_message_length"]
    ev = event.RegularEvent.build(
        keys,
        kind=1000,
        content="a" * (max_supported_size + 1),
    )

    await request_queue.put(event_message.Event.from_event(ev).serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, notice.Notice)


async def test_request_too_many_filters_errors(
    relay_info, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "max_filters")

    max_supported_size = relay_info["limitation"]["max_filters"]
    req = request.Request("1", [{} for _ in range(max_supported_size + 1)])

    await request_queue.put(req.serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, notice.Notice)


async def test_request_filter_limit_too_large_errors(
    relay_info, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "max_limit")

    max_supported_size = relay_info["limitation"]["max_limit"]
    req = request.Request("1", [{"limit": max_supported_size + 1}])

    await request_queue.put(req.serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, notice.Notice)


async def test_request_filter_id_prefix_too_small(
    relay_info, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "min_prefix")

    min_supported_size = relay_info["limitation"]["min_prefix"]
    req = request.Request("1", [{"ids": ["a" * (min_supported_size - 1)]}])

    await request_queue.put(req.serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, notice.Notice)


async def test_request_filter_author_prefix_too_small(
    relay_info, request_queue, response_queue
):
    skip_if_no_field(relay_info, "limitation", "min_prefix")

    min_supported_size = relay_info["limitation"]["min_prefix"]
    req = request.Request("1", [{"authors": ["a" * (min_supported_size - 1)]}])

    await request_queue.put(req.serialize())
    msg = message_factory.from_str(await response_queue.get())
    assert isinstance(msg, notice.Notice)
