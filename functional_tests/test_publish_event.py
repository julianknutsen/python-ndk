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

# pylint: disable=redefined-outer-name, protected-access

import pytest

from ndk import crypto
from ndk.event import event, metadata_event
from ndk.messages import event_message
from ndk.repos.event_repo import event_repo


@pytest.fixture()
def fake_repo(ev_repo):
    return ev_repo


@pytest.fixture()
def real_repo(relay_ev_repo):
    return relay_ev_repo


@pytest.fixture(params=["fake_repo", "real_repo"])
def repo(request):
    return request.getfixturevalue(request.param)


@pytest.fixture()
def unsigned_event():
    return metadata_event.MetadataEvent.from_metadata_parts(
        "bob", "#nostr", "http://pics.com"
    )


@pytest.fixture()
def signed_event(unsigned_event):
    keys = crypto.KeyPair()
    return event.build_signed_event(unsigned_event, keys)


@pytest.fixture()
def signed_event2(unsigned_event):
    keys = crypto.KeyPair()
    return event.build_signed_event(unsigned_event, keys)


fields = ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"]


# XXX only runs on fake right now due to relayer bug
@pytest.mark.parametrize("field", fields)
async def test_publish_event_missing_field_returns_notice(
    field,
    unsigned_event,
    fake_repo,  # pylint: disable=unused-argument
    protocol_rq,
    protocol_wq,
    caplog,
):
    keys = crypto.KeyPair()

    signed_ev = event.build_signed_event(unsigned_event, keys)
    serializable = signed_ev.__dict__
    del serializable[field]

    await protocol_wq.put(event_message.Event.from_signed_event(signed_ev).serialize())
    await protocol_wq.join()
    await protocol_rq.join()

    assert "Unable to parse message" in caplog.text


async def test_set_metadata_invalid_sig_is_not_accepted(
    repo, signed_event, signed_event2
):
    object.__setattr__(signed_event, "sig", signed_event2.sig)

    with pytest.raises(event_repo.AddItemError):
        await repo.add(signed_event)


# XXX only runs on fake right now due to relayer bug
async def test_set_metadata_invalid_id_is_not_accepted(
    fake_repo, signed_event, signed_event2
):
    assert signed_event.id != signed_event2.id
    object.__setattr__(signed_event, "id", signed_event2.id)

    with pytest.raises(event_repo.AddItemError):
        await fake_repo.add(signed_event)


async def build_sign_publish_metadata_event(repo, *args, **kwargs):
    keys = crypto.KeyPair()

    unsigned_event = metadata_event.MetadataEvent.from_metadata_parts(*args, **kwargs)
    signed_event = event.build_signed_event(unsigned_event, keys)

    assert await repo.add(signed_event)


async def test_set_metadata_only_name_present_is_accepted(repo):
    await build_sign_publish_metadata_event(repo, name="bob")


async def test_set_metadata_only_about_present(repo):
    await build_sign_publish_metadata_event(repo, about="#nostr")


async def test_set_metadata_only_picture_present(repo):
    await build_sign_publish_metadata_event(repo, picture="foo")


async def test_set_metadata_no_content(repo):
    await build_sign_publish_metadata_event(repo)
