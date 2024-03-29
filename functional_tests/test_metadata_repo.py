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

import testing_utils
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
def local(local_ev_repo):
    return event_backed_metadata_repo.EventBackedMetadataRepo(local_ev_repo)


@pytest.fixture
def remote(remote_ev_repo):
    return event_backed_metadata_repo.EventBackedMetadataRepo(remote_ev_repo)


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

    async def verify_name():
        ret = await repo.get(mykeys.public)
        assert "name" in ret and ret["name"] == "bob"

    await testing_utils.retry_on_assert_coro(verify_name)


async def test_overwrite(mykeys, repo):
    cur = time.time()
    with mock.patch("time.time", return_value=cur):
        await repo.overwrite(mykeys, name="bob")

    with mock.patch("time.time", return_value=cur + 1):
        await repo.overwrite(mykeys, about="#nostr")

    async def verify_about():
        assert (await repo.get(mykeys.public)).get("about") == "#nostr"

    await testing_utils.retry_on_assert_coro(verify_about)


async def test_overwrite_recommend_server(mykeys, repo):
    await repo.overwrite(mykeys, recommend_server="ws://foo.com")

    async def verify_server():
        assert (await repo.get(mykeys.public))["recommend_server"] == "ws://foo.com"

    await testing_utils.retry_on_assert_coro(verify_server)


async def test_overwrite_metadata_spanning_multiple_events(mykeys, repo):
    cur = time.time()
    with mock.patch("time.time", return_value=cur):
        await repo.overwrite(mykeys, name="bob")

    with mock.patch("time.time", return_value=cur + 1):
        await repo.overwrite(mykeys, recommend_server="ws://foo.com")

    async def verify_server():
        with mock.patch("time.time", return_value=cur + 2):
            assert (await repo.get(mykeys.public))["recommend_server"] == "ws://foo.com"

    await testing_utils.retry_on_assert_coro(verify_server)


async def test_overwrite_contact_list(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public, "", "")

    await repo.overwrite(mykeys, contact_list=contact_list)

    async def verify_contacts():
        assert (await repo.get(mykeys.public))["contacts"] == contact_list

    await testing_utils.retry_on_assert_coro(verify_contacts)


async def test_overwrite_contact_list_only_pubkey(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public)

    await repo.overwrite(mykeys, contact_list=contact_list)

    async def verify_contacts():
        assert (await repo.get(mykeys.public))["contacts"] == contact_list

    await testing_utils.retry_on_assert_coro(verify_contacts)
