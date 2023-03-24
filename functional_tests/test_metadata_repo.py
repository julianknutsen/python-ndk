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
import time

import mock
import pytest

from ndk import crypto
from ndk.repos import contacts
from ndk.repos.metadata_repo import event_backed_metadata_repo, fake_metadata_repo


@pytest.fixture
def mykeys():
    return crypto.KeyPair()


@pytest.fixture
def mypub(mykeys):
    return crypto.PublicKeyStr(mykeys.public)


@pytest.fixture
def fake():
    return fake_metadata_repo.FakeMetadataRepository()


@pytest.fixture
def local(local_relay, ev_repo):
    return event_backed_metadata_repo.EventBackedMetadataRepo(ev_repo)


@pytest.fixture
def remote(remote_relay, ev_repo):
    return event_backed_metadata_repo.EventBackedMetadataRepo(ev_repo)


@pytest.fixture(params=["fake", "local", "remote"])
def repo(request):
    return request.getfixturevalue(request.param)


async def test_initial_state(repo):
    theirkeys = crypto.KeyPair()
    assert await repo.get(theirkeys.public) == {
        "recommend_server": "",
        "contacts": contacts.ContactList(),
    }


async def test_overwrite_write(mykeys, repo):
    await repo.overwrite(mykeys, name="bob")

    assert (await repo.get(mykeys.public))["name"] == "bob"


async def test_overwrite(mykeys, repo):
    await repo.overwrite(mykeys, name="bob")
    await repo.overwrite(mykeys, about="#nostr")

    result = await repo.get(mykeys.public)
    assert result["about"] == "#nostr"


async def test_overwrite_recommend_server(mykeys, repo):
    await repo.overwrite(mykeys, recommend_server="ws://foo.com")

    assert (await repo.get(mykeys.public))["recommend_server"] == "ws://foo.com"


async def test_overwrite_metadata_spanning_multiple_events(mykeys, repo):
    cur = time.time()
    with mock.patch("time.time", return_value=cur):
        await repo.overwrite(mykeys, name="bob")

    with mock.patch("time.time", return_value=cur + 1):
        await repo.overwrite(mykeys, recommend_server="ws://foo.com")

    with mock.patch("time.time", return_value=cur + 2):
        assert (await repo.get(mykeys.public))["recommend_server"] == "ws://foo.com"


async def test_overwrite_contact_list(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public, "", "")

    await repo.overwrite(mykeys, contact_list=contact_list)

    assert (await repo.get(mykeys.public))["contacts"] == contact_list


async def test_overwrite_contact_list_only_pubkey(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public)

    await repo.overwrite(mykeys, contact_list=contact_list)

    assert (await repo.get(mykeys.public))["contacts"] == contact_list
