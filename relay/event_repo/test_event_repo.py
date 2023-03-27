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
import time

import mock
import pytest

from ndk import crypto
from ndk.event import event, metadata_event, text_note_event
from relay.event_repo import memory_event_repo, postgres_event_repo


@pytest.fixture
def fake():
    return memory_event_repo.MemoryEventRepo()


@pytest.fixture
def postgres(db_url):
    return asyncio.get_event_loop().run_until_complete(
        postgres_event_repo.PostgresEventRepo.create(
            db_url, 5432, "nostr", "nostr", "nostr"
        )
    )


@pytest.fixture(params=["fake", "postgres"])
def repo(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def keys():
    return crypto.KeyPair()


@pytest.fixture
def unsigned():
    return metadata_event.MetadataEvent.from_metadata_parts()


@pytest.fixture
def signed(keys, unsigned):
    return event.build_signed_event(unsigned, keys)


async def test_get_empty(repo):
    items = await repo.get([{}])

    assert len(items) == 0


async def test_get_matches_by_id(repo, signed):
    ev_id = await repo.add(signed)

    items = await repo.get([{"ids": [ev_id]}])

    assert len(items) == 1
    assert items[0] == signed


async def test_get_matches_by_author(repo, keys, signed):
    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public]}])

    assert len(items) == 1
    assert items[0] == signed


async def test_get_matches_by_author_and_id(repo, keys, signed):
    ev_id = await repo.add(signed)

    items = await repo.get([{"ids": [ev_id], "authors": [keys.public]}])

    assert len(items) == 1
    assert items[0] == signed


async def test_get_matches_by_id_only_last(repo, keys):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        unsigned1 = metadata_event.MetadataEvent.from_metadata_parts()
        signed1 = event.build_signed_event(unsigned1, keys)

    with mock.patch("time.time", return_value=cur + 1):
        unsigned2 = metadata_event.MetadataEvent.from_metadata_parts()
        signed2 = event.build_signed_event(unsigned2, keys)

    _ = await repo.add(signed1)
    _ = await repo.add(signed2)

    items = await repo.get([{"authors": [keys.public], "limit": 1}])

    assert len(items) == 1
    assert items[0] == signed2


async def test_get_matches_by_id_limit_greater(repo, signed, keys):
    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public], "limit": 2}])

    assert len(items) == 1
    assert items[0] == signed


async def test_get_no_matches_by_etag(repo, signed, keys):
    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public], "#e": [keys.public]}])

    assert len(items) == 0


def build_signed_text_note(keys, tags=None):
    if not tags:
        tags = [[]]

    unsigned = text_note_event.TextNoteEvent.from_content(
        "Hello, world!", tags=event.EventTags(tags)
    )
    return event.build_signed_event(unsigned, keys)


async def test_matches_by_etag(repo, keys):
    signed = build_signed_text_note(keys, [["e", keys.public]])

    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public], "#e": [keys.public]}])

    assert len(items) == 1


async def test_matches_by_etag_event_has_multiple_tags(repo, keys):
    signed = build_signed_text_note(keys, [["e", keys.public], ["p", keys.public]])

    _ = await repo.add(signed)

    items1 = await repo.get([{"authors": [keys.public], "#e": [keys.public]}])
    items2 = await repo.get([{"authors": [keys.public], "#p": [keys.public]}])

    assert len(items1) == 1
    assert len(items2) == 1


async def test_get_no_matches_by_ptag(repo, keys):
    signed = build_signed_text_note(keys)

    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public], "#p": [keys.public]}])

    assert len(items) == 0


async def test_matches_by_ptag(repo, keys):
    signed = build_signed_text_note(keys, [["p", keys.public]])

    _ = await repo.add(signed)

    items = await repo.get([{"authors": [keys.public], "#p": [keys.public]}])

    assert len(items) == 1


async def test_matches_by_ptags(repo, keys):
    signed = build_signed_text_note(keys, [["p", keys.public, "ws://foo"]])
    keys2 = crypto.KeyPair()
    signed2 = build_signed_text_note(keys, [["p", keys2.public]])

    _ = await repo.add(signed)
    _ = await repo.add(signed2)

    items = await repo.get(
        [{"authors": [keys.public], "#p": [keys.public, keys2.public]}]
    )

    assert len(items) == 2


async def test_matches_multiple_filters_or(repo, keys):
    signed = build_signed_text_note(keys)
    keys2 = crypto.KeyPair()
    signed2 = build_signed_text_note(keys2)

    _ = await repo.add(signed)
    _ = await repo.add(signed2)

    items = await repo.get([{"authors": [keys.public]}, {"authors": [keys2.public]}])

    assert len(items) == 2
