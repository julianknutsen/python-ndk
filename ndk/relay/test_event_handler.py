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

from ndk.event import event
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
    ev = mock.MagicMock(spec=event.RegularEvent, id="1")
    await eh.handle_event(ev)

    repo.add.assert_called_once_with(ev)
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(ev)


async def test_handle_replaceable_event_behavior(repo, notifier, eh):
    existing_ev = mock.MagicMock(
        event.ReplaceableEvent, id="1", kind=0, pubkey="1", created_at=1, tags=[]
    )
    await repo.add(existing_ev)
    repo.reset_mock()

    newer_ev = mock.MagicMock(
        event.ReplaceableEvent, id="2", kind=0, pubkey="1", created_at=2, tags=[]
    )
    await eh.handle_event(newer_ev)

    repo.add.assert_called_once_with(newer_ev)
    repo.remove.assert_called_once_with("1")
    notifier.handle_event.assert_called_once_with(newer_ev)


async def test_handle_ephemeral_event_behavior(repo, notifier, eh):
    ev = mock.MagicMock(event.EphemeralEvent)
    await eh.handle_event(ev)

    repo.add.assert_not_called()
    repo.remove.assert_not_called()
    notifier.handle_event.assert_called_once_with(ev)


async def test_handle_basic_event_behavior(repo, notifier, eh):
    ev = mock.MagicMock(event.Event)
    await eh.handle_event(ev)

    repo.add.assert_not_called()
    repo.remove.assert_not_called()
    notifier.handle_event.assert_not_called()


async def test_no_register_not_called(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent)
    cb = mock.AsyncMock()

    await real_eh.handle_event(ev)

    cb.assert_not_called()


async def test_register_cb_called(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent)
    cb = mock.AsyncMock()
    real_eh.register_received_cb(cb)

    await real_eh.handle_event(ev)

    cb.assert_called_once_with(ev)


async def test_insert_callback_after_unregister(real_eh):
    ev = mock.MagicMock(event.EphemeralEvent)
    cb = mock.AsyncMock()
    cb_id = real_eh.register_received_cb(cb)
    real_eh.unregister_received_cb(cb_id)

    await real_eh.handle_event(ev)

    cb.assert_not_called()
