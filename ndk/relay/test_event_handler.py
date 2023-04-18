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

import mock
import pytest

from ndk import exceptions
from ndk.event import event, event_tags
from ndk.event import parameterized_replaceable_event as pre
from ndk.relay import event_handler, event_notifier
from ndk.relay.event_repo import memory_event_repo


@pytest.fixture
def repo():
    return mock.AsyncMock(wraps=memory_event_repo.MemoryEventRepo())


@pytest.fixture
def notifier():
    return mock.AsyncMock(wraps=event_notifier.EventNotifier())


@pytest.fixture
def eh(repo, notifier):
    return event_handler.EventHandler(repo, notifier)


@pytest.fixture
def real_eh():
    repo = memory_event_repo.MemoryEventRepo()
    notifier = event_notifier.EventNotifier()
    return event_handler.EventHandler(repo, notifier)


def test_init(repo, notifier, eh):
    pass  # fixtures do the work


async def test_handle_regular_event_behavior(repo, notifier, eh):
    ev = mock.MagicMock(spec=event.RegularEvent, id="1", content="")
    await eh.handle_event(ev)

    repo.add.assert_called_once_with(ev)
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(ev)


async def test_over_default_content_length(eh):
    ev = mock.MagicMock(spec=event.RegularEvent, id="1", content="a" * 8197)
    with pytest.raises(exceptions.ValidationError, match="greater than 8196 bytes"):
        await eh.handle_event(ev)


async def test_over_overridden_content_length():
    repo = memory_event_repo.MemoryEventRepo()
    notifier = event_notifier.EventNotifier()
    eh = event_handler.EventHandler(repo, notifier, event_handler.EventHandlerConfig(0))
    ev = mock.MagicMock(spec=event.RegularEvent, id="1", content="a")
    with pytest.raises(exceptions.ValidationError, match="greater than 0 bytes"):
        await eh.handle_event(ev)


async def test_handle_replaceable_event_behavior(repo, notifier, eh):
    existing_ev = mock.MagicMock(
        event.ReplaceableEvent,
        id="1",
        kind=0,
        pubkey="1",
        created_at=1,
        content="",
        tags=[],
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = mock.MagicMock(
        event.ReplaceableEvent,
        id="2",
        kind=0,
        pubkey="1",
        created_at=2,
        content="",
        tags=[],
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_called_once_with("1")
    notifier.handle_event.assert_called_once_with(newer_ev)


async def test_handle_ephemeral_event_behavior(repo, notifier, eh):
    ev = mock.MagicMock(event.EphemeralEvent, content="")
    await eh.handle_event(ev)

    repo.add.assert_not_called()
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(ev)


async def test_handle_basic_event_behavior(repo, notifier, eh):
    ev = mock.MagicMock(event.Event, content="")
    await eh.handle_event(ev)

    repo.add.assert_not_called()
    repo.remove.assert_not_called()
    notifier.handle_event.assert_not_called()


async def test_no_register_not_called(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent, content="")
    cb = mock.AsyncMock()

    await real_eh.handle_event(ev)

    cb.assert_not_called()


async def test_register_cb_called(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent, content="")
    cb = mock.AsyncMock()
    real_eh.register_received_cb(cb)

    await real_eh.handle_event(ev)

    cb.assert_called_once_with(ev)


async def test_insert_callback_after_unregister(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent, content="")
    cb = mock.AsyncMock()
    cb_id = real_eh.register_received_cb(cb)
    real_eh.unregister_received_cb(cb_id)

    await real_eh.handle_event(ev)

    cb.assert_not_called()


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
    tags, keys, repo, notifier, eh
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_called_once_with(existing_ev.id)
    notifier.handle_event.assert_called_once_with(newer_ev)


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
    tags, keys, repo, notifier, eh
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", ""]])
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_called_once_with(existing_ev.id)
    notifier.handle_event.assert_called_once_with(newer_ev)


async def test_handle_parameterized_replaceable_event_behavior_empty_d_not_replaced(
    keys, repo, notifier, eh
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=event_tags.EventTags([["d", "foo"]])
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(newer_ev)


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
    tags, keys, repo, notifier, eh
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=tags
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(newer_ev)


async def test_handle_parameterized_replaceable_event_behavior_valid_d_replaced(
    keys, repo, notifier, eh
):
    existing_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=1, tags=event_tags.EventTags([["d", "foo"]])
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = pre.ParameterizedReplaceableEvent.build(
        keys, kind=30000, created_at=2, tags=event_tags.EventTags([["d", "foo"]])
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_called_once_with(existing_ev.id)
    notifier.handle_event.assert_called_once_with(newer_ev)
