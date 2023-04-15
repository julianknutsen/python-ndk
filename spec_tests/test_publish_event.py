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

import pytest

from ndk import crypto
from ndk.event import metadata_event
from ndk.messages import event_message, message_factory, notice
from ndk.repos.event_repo import event_repo


@pytest.fixture
def local(local_ev_repo):
    return local_ev_repo


@pytest.fixture
def remote(remote_ev_repo):
    return remote_ev_repo


@pytest.fixture(params=["local", "remote"])
def repo(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def local_relay(local_relay):
    yield


@pytest.fixture
def remote_relay(remote_relay):
    yield


@pytest.fixture(params=["local_relay", "remote_relay"])
def relay(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def event(keys):
    return metadata_event.MetadataEvent.from_metadata_parts(
        keys, "bob", "#nostr", "http://pics.com"
    )


@pytest.fixture
def event2():
    keys = crypto.KeyPair()
    return metadata_event.MetadataEvent.from_metadata_parts(
        keys, "bob", "#nostr", "http://pics.com"
    )


fields = ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"]


@pytest.mark.usefixtures("relay")  #
@pytest.mark.parametrize("field", fields)
async def test_publish_event_missing_field_returns_notice(
    field,
    event,
    response_queue,
    request_queue,
):
    serializable = event.__dict__
    del serializable[field]

    await request_queue.put(event_message.Event.from_event(event).serialize())

    n = message_factory.from_str(await response_queue.get())
    assert isinstance(n, notice.Notice)
    assert "Unable to parse message" in n.message


async def test_set_metadata_invalid_sig_is_not_accepted(repo, event, event2):
    object.__setattr__(event, "sig", event2.sig)

    with pytest.raises(event_repo.AddItemError):
        await repo.add(event)


async def test_set_metadata_invalid_id_is_not_accepted(repo, event, event2):
    assert event.id != event2.id
    object.__setattr__(event, "id", event2.id)

    with pytest.raises(event_repo.AddItemError):
        await repo.add(event)


async def build_sign_publish_metadata_event(repo, *args, **kwargs):
    keys = crypto.KeyPair()

    event = metadata_event.MetadataEvent.from_metadata_parts(keys, *args, **kwargs)

    assert await repo.add(event)


async def test_set_metadata_only_name_present_is_accepted(repo):
    await build_sign_publish_metadata_event(repo, name="bob")


async def test_set_metadata_only_about_present(repo):
    await build_sign_publish_metadata_event(repo, about="#nostr")


async def test_set_metadata_only_picture_present(repo):
    await build_sign_publish_metadata_event(repo, picture="foo")


async def test_set_metadata_no_content(repo):
    await build_sign_publish_metadata_event(repo)
