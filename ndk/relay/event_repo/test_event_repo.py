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
from ndk.event import event, event_filter, event_tags, metadata_event
from ndk.event import parameterized_replaceable_event as pre
from ndk.event import text_note_event
from ndk.relay.event_repo import memory_event_repo, mysql_event_repo


@pytest.fixture
def fake():
    return memory_event_repo.MemoryEventRepo()


@pytest.fixture
def db(db_url):
    return asyncio.get_event_loop().run_until_complete(
        mysql_event_repo.MySqlEventRepo.create(db_url, 3306, "nostr", "nostr", "nostr")
    )


@pytest.fixture(params=["fake", "db"])
def repo(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def metadata_ev(keys):
    return metadata_event.MetadataEvent.from_metadata_parts(keys)


async def test_get_empty(repo):
    items = await repo.get([event_filter.EventFilter()])

    assert len(items) == 0


async def test_get_matches_by_id(repo, metadata_ev):
    ev_id = await repo.add(metadata_ev)

    items = await repo.get([event_filter.EventFilter(ids=[ev_id])])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_duplicate_insert_one_result(repo, metadata_ev):
    ev_id1 = await repo.add(metadata_ev)
    ev_id2 = await repo.add(metadata_ev)
    assert ev_id1 == ev_id2

    items = await repo.get([event_filter.EventFilter(ids=[ev_id1])])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_matches_by_id_prefix(repo, metadata_ev):
    ev_id = await repo.add(metadata_ev)

    items = await repo.get([event_filter.EventFilter(ids=[ev_id[0]])])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_matches_by_author(repo, keys, metadata_ev):
    _ = await repo.add(metadata_ev)

    items = await repo.get([event_filter.EventFilter(authors=[keys.public])])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_matches_by_author_prefix(repo, keys, metadata_ev):
    _ = await repo.add(metadata_ev)

    items = await repo.get([event_filter.EventFilter(authors=[keys.public[:3]])])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_matches_by_author_and_id(repo, keys, metadata_ev):
    ev_id = await repo.add(metadata_ev)

    items = await repo.get(
        [event_filter.EventFilter(ids=[ev_id], authors=[keys.public])]
    )

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_matches_by_id_only_last(repo, keys):
    cur = int(time.time())
    with mock.patch("time.time", return_value=cur):
        event1 = metadata_event.MetadataEvent.from_metadata_parts(keys)

    with mock.patch("time.time", return_value=cur + 1):
        event2 = metadata_event.MetadataEvent.from_metadata_parts(keys)

    _ = await repo.add(event1)
    _ = await repo.add(event2)

    items = await repo.get([event_filter.EventFilter(authors=[keys.public], limit=1)])

    assert len(items) == 1
    assert items[0] == event2


async def test_get_matches_by_id_limit_greater(repo, metadata_ev, keys):
    _ = await repo.add(metadata_ev)

    items = await repo.get([event_filter.EventFilter(authors=[keys.public], limit=2)])

    assert len(items) == 1
    assert items[0] == metadata_ev


async def test_get_no_matches_by_etag(repo, metadata_ev, keys):
    _ = await repo.add(metadata_ev)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"e": [keys.public]}
            )
        ]
    )

    assert len(items) == 0


def build_text_note(keys, tags=None):
    if not tags:
        tags = []

    return text_note_event.TextNoteEvent.from_content(
        keys, "Hello, world!", tags=event_tags.EventTags(tags)
    )


async def test_matches_by_etag(repo, keys):
    event = build_text_note(keys, [["e", keys.public]])

    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"e": [keys.public]}
            )
        ]
    )

    assert len(items) == 1
    assert items[0] == event


async def test_matches_by_etag_duplicated(repo, keys):
    event = build_text_note(keys, [["e", keys.public], ["e", keys.public]])

    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"e": [keys.public]}
            )
        ]
    )

    assert len(items) == 1
    assert items[0] == event


async def test_matches_by_etag_event_has_multiple_tags(repo, keys):
    event = build_text_note(keys, [["e", keys.public], ["p", keys.public]])

    _ = await repo.add(event)

    items1 = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"e": [keys.public]}
            )
        ]
    )
    items2 = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"p": [keys.public]}
            )
        ]
    )

    assert len(items1) == 1
    assert items1[0] == event
    assert len(items2) == 1
    assert items2[0] == event


async def test_get_no_matches_by_ptag(repo, keys):
    event = build_text_note(keys)

    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"p": [keys.public]}
            )
        ]
    )

    assert len(items) == 0


async def test_matches_by_ptag(repo, keys):
    event = build_text_note(keys, [["p", keys.public]])

    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"p": [keys.public]}
            )
        ]
    )

    assert len(items) == 1
    assert items[0] == event


async def test_matches_by_ptag_with_relay(repo, keys):
    event = build_text_note(keys, [["p", keys.public, "ws://foo"]])

    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"p": [keys.public]}
            )
        ]
    )

    assert len(items) == 1
    assert items[0] == event


async def test_matches_by_ptags(repo, keys):
    event = build_text_note(keys, [["p", keys.public, "ws://foo"]])
    keys2 = crypto.KeyPair()
    event2 = build_text_note(keys, [["p", keys2.public]])

    _ = await repo.add(event)
    _ = await repo.add(event2)

    items = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], generic_tags={"p": [keys.public, keys2.public]}
            )
        ]
    )

    assert len(items) == 2


async def test_matches_multiple_filters_or(repo, keys):
    event = build_text_note(keys)
    keys2 = crypto.KeyPair()
    event2 = build_text_note(keys2)

    _ = await repo.add(event)
    _ = await repo.add(event2)

    items = await repo.get(
        [
            event_filter.EventFilter(authors=[keys.public]),
            event_filter.EventFilter(authors=[keys2.public]),
        ]
    )

    assert len(items) == 2


async def test_multiple_filters_match_same_event_returns_one(repo, keys):
    event = build_text_note(keys)
    _ = await repo.add(event)

    items = await repo.get(
        [
            event_filter.EventFilter(authors=[keys.public]),
            event_filter.EventFilter(authors=[keys.public]),
        ]
    )

    assert len(items) == 1


async def test_delete_with_no_entry_raises(repo):
    with pytest.raises(ValueError):
        await repo.remove("foo")


async def test_delete_deletes(repo, metadata_ev):
    ev_id = await repo.add(metadata_ev)
    await repo.remove(ev_id)
    events = await repo.get([event_filter.EventFilter(ids=[ev_id])])
    assert len(events) == 0


async def test_delete_with_tags_deletes(keys, repo):
    ev = event.RegularEvent.build(
        keys, kind=10001, tags=event_tags.EventTags([["foo", "bar"]])
    )
    ev_id = await repo.add(ev)
    await repo.remove(ev_id)
    events = await repo.get([event_filter.EventFilter(ids=[ev_id])])
    assert len(events) == 0


@pytest.mark.parametrize(
    "tags",
    [
        None,
        event_tags.EventTags([["d", ""]]),
        event_tags.EventTags([["d", ""], ["d", "not empty"]]),
        event_tags.EventTags([["d", "", "123"]]),
    ],
)
async def test_handle_parameterized_replaceable_event_behavior_empty_d(
    tags,
    keys,
    repo,
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", ""]])
    )
    await repo.add(existing_ev)

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await repo.add(newer_ev)

    evs = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], kinds=[30000], generic_tags={"d": [""]}
            ),
            event_filter.EventFilter(authors=[keys.public], kinds=[30000]),
        ]
    )
    assert evs[0] == newer_ev


@pytest.mark.parametrize(
    "tags",
    [
        None,
        event_tags.EventTags([["d", ""]]),
        event_tags.EventTags([["d", ""], ["d", "not empty"]]),
        event_tags.EventTags([["d", "", "123"]]),
    ],
)
async def test_handle_parameterized_replaceable_event_behavior_no_tags(
    tags, keys, repo
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1
    )
    await repo.add(existing_ev)

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await repo.add(newer_ev)

    evs = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], kinds=[30000], generic_tags={"d": [""]}
            ),
            event_filter.EventFilter(authors=[keys.public], kinds=[30000]),
        ]
    )
    assert len(evs) == 1
    assert evs[0] == newer_ev


async def test_handle_parameterized_replaceable_event_behavior_empty_d_not_replaced(
    keys, repo
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1
    )
    await repo.add(existing_ev)

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(newer_ev)

    evs = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], kinds=[30000], generic_tags={"d": [""]}
            ),
            event_filter.EventFilter(authors=[keys.public], kinds=[30000]),
        ]
    )
    assert len(evs) == 2
    assert evs[0] == newer_ev
    assert evs[1] == existing_ev


@pytest.mark.parametrize(
    "tags",
    [
        None,
        event_tags.EventTags([["d", ""]]),
        event_tags.EventTags([["d", ""], ["d", "not empty"]]),
        event_tags.EventTags([["d", "", "123"]]),
    ],
)
async def test_handle_parameterized_replaceable_event_behavior_not_replaced(
    tags, keys, repo
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(existing_ev)

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await repo.add(newer_ev)

    evs = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], kinds=[30000], generic_tags={"d": [""]}
            ),
            event_filter.EventFilter(authors=[keys.public], kinds=[30000]),
        ]
    )
    assert len(evs) == 2
    assert evs[0] == newer_ev
    assert evs[1] == existing_ev


async def test_handle_parameterized_replaceable_event_behavior_valid_d_replaced(
    keys, repo
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(existing_ev)

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(newer_ev)

    evs = await repo.get(
        [
            event_filter.EventFilter(
                authors=[keys.public], kinds=[30000], generic_tags={"d": [""]}
            ),
            event_filter.EventFilter(authors=[keys.public], kinds=[30000]),
        ]
    )
    assert len(evs) == 1
    assert evs[0] == newer_ev
