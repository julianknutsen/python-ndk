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

from ndk.relay.event_repo import event_notifier


def test_init():
    event_notifier.EventNotifier()


async def test_register_callback_is_called():
    h = event_notifier.EventNotifier()

    cb = mock.AsyncMock(spec=event_notifier.EventNotifierCb)
    h.register(cb)

    ev = mock.AsyncMock()
    await h.handle_event(ev)
    assert cb.called


async def test_register_callback_twice_both_called():
    h = event_notifier.EventNotifier()

    cb = mock.AsyncMock(spec=event_notifier.EventNotifierCb)
    cb2 = mock.AsyncMock(spec=event_notifier.EventNotifierCb)
    h.register(cb)
    h.register(cb2)

    ev = mock.AsyncMock()
    await h.handle_event(ev)
    assert cb.called
    assert cb2.called


async def test_register_callback_is_not_called_after_unregister():
    h = event_notifier.EventNotifier()

    cb = mock.AsyncMock(spec=event_notifier.EventNotifierCb)
    cb_id = h.register(cb)

    ev = mock.AsyncMock()
    await h.handle_event(ev)
    cb.assert_called_once_with(ev)

    cb.reset_mock()
    h.unregister(cb_id)
    await h.handle_event(ev)
    cb.assert_not_called()


async def test_unregister_with_bad_cbid_raises():
    h = event_notifier.EventNotifier()
    with pytest.raises(ValueError):
        h.unregister(event_notifier.EventNotifierCbId("unknown cb id"))
