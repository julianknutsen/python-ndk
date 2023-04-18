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

import asyncio

import mock
import pytest

from ndk.event import metadata_event
from ndk.relay import subscription_handler


def test_init():
    subscription_handler.SubscriptionHandler(asyncio.Queue())


async def test_clear_before_set_no_output():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)
    await sh.clear_filters("subid")

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = False
    await sh.set_filters("subid", [fltr])

    ev = mock.MagicMock()
    await sh.handle_event(ev)
    assert q.empty()


async def test_no_output_with_no_filter():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    ev = mock.MagicMock()
    await sh.handle_event(ev)
    assert q.empty()


async def test_no_output_with_wrong_filter():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = False
    await sh.set_filters("subid", [fltr])

    ev = mock.MagicMock()
    await sh.handle_event(ev)
    assert q.empty()


async def test_output_with_matching_filter(keys):
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = True
    await sh.set_filters("subid", [fltr])

    event = metadata_event.MetadataEvent.from_metadata_parts(keys=keys)
    await sh.handle_event(event)
    assert not q.empty()


async def test_two_output_with_two_matching_filter(keys):
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = True
    await sh.set_filters("subid", [fltr])
    await sh.set_filters("subid2", [fltr])

    event = metadata_event.MetadataEvent.from_metadata_parts(keys=keys)
    await sh.handle_event(event)
    assert q.qsize() == 2


async def test_output_with_filter_overwrite():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = True
    await sh.set_filters("subid", [fltr])

    fltr2 = mock.MagicMock()
    fltr2.matches_event.return_value = False
    await sh.set_filters("subid", [fltr2])

    ev = mock.MagicMock()
    await sh.handle_event(ev)
    assert q.empty()


async def test_no_output_with_matching_filter_after_clear():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    fltr.matches_event.return_value = True
    await sh.set_filters("subid", [fltr])
    await sh.clear_filters(
        "subid",
    )

    ev = mock.MagicMock()
    await sh.handle_event(ev)
    assert q.empty()


async def test_more_than_max_subs_default():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(q)

    fltr = mock.MagicMock()
    with pytest.raises(subscription_handler.SubscriptionLimitExceeded):
        for i in range(21):
            await sh.set_filters(f"subid{i}", [fltr])


async def test_more_than_max_subs_override():
    q = asyncio.Queue()
    sh = subscription_handler.SubscriptionHandler(
        q, subscription_handler.SubscriptionHandlerConfig(0)
    )

    fltr = mock.MagicMock()
    with pytest.raises(subscription_handler.SubscriptionLimitExceeded):
        await sh.set_filters("subid", [fltr])
