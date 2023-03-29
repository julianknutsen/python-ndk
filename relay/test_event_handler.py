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

import mock
import pytest

from ndk.event import event, metadata_event
from relay import event_handler
from relay.event_repo import memory_event_repo


def test_init():
    repo = mock.AsyncMock()
    event_handler.EventHandler(repo)


async def test_handle_event_metadata_saves():
    repo = mock.AsyncMock()
    eh = event_handler.EventHandler(repo)

    ev = mock.MagicMock(type=metadata_event.MetadataEvent)
    await eh.handle_event(ev)

    repo.add.assert_called_once_with(ev)


async def test_handle_event_text_note_saves():
    repo = mock.AsyncMock()
    eh = event_handler.EventHandler(repo)

    ev = mock.MagicMock()
    await eh.handle_event(ev)

    repo.add.assert_called_once_with(ev)


async def test_handle_contact_list_saves():
    repo = mock.AsyncMock()
    eh = event_handler.EventHandler(repo)

    ev = mock.MagicMock()
    await eh.handle_event(ev)

    repo.add.assert_called_once_with(ev)


@pytest.mark.parametrize(
    "kind", [event.EventKind.CONTACT_LIST, event.EventKind.SET_METADATA]
)
async def test_handle_contact_list_deletes_old(kind):
    repo = mock.AsyncMock(wraps=memory_event_repo.MemoryEventRepo())
    eh = event_handler.EventHandler(repo)

    ev_old = mock.MagicMock(kind=kind, pubkey="pubkey", created_at=1)
    await eh.handle_event(ev_old)

    ev_new = mock.MagicMock(kind=kind, pubkey="pubkey", created_at=2)
    await eh.handle_event(ev_new)

    repo.add.assert_has_calls([mock.call(ev_old), mock.call(ev_new)])
    repo.remove.assert_called_once_with(ev_old.id)
