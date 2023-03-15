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
import time

import mock
import pytest

from ndk import crypto
from ndk.repos import contacts
from ndk.repos.metadata_repo import event_backed_metadata_repo, fake_metadata_repo


@pytest.fixture()
def mykeys():
    return crypto.KeyPair()


@pytest.fixture()
def mypub(mykeys):
    return crypto.PublicKeyStr(mykeys.public)


@pytest.fixture()
def fake_repo():
    return fake_metadata_repo.FakeMetadataRepository()


@pytest.fixture()
def real_repo(relay_ev_repo):
    return event_backed_metadata_repo.EventBackedMetadataRepo(relay_ev_repo)


@pytest.fixture(params=["fake_repo", "real_repo"])
def repo(request):
    return request.getfixturevalue(request.param)


def test_initial_state(repo):
    theirkeys = crypto.KeyPair()
    assert repo.get(theirkeys.public) == {
        "recommend_server": "",
        "contacts": contacts.ContactList(),
    }


def test_overwrite_write(mykeys, repo):
    repo.overwrite(mykeys, name="bob")

    assert repo.get(mykeys.public)["name"] == "bob"


def test_overwrite(mykeys, repo):
    repo.overwrite(mykeys, name="bob")
    repo.overwrite(mykeys, about="#nostr")

    assert repo.get(mykeys.public)["about"] == "#nostr"


def test_overwrite_recommend_server(mykeys, repo):
    repo.overwrite(mykeys, recommend_server="ws://foo.com")

    assert repo.get(mykeys.public)["recommend_server"] == "ws://foo.com"


def test_overwrite_metadata_spanning_multiple_events(mykeys, repo):
    cur = time.time()
    with mock.patch("time.time", return_value=cur):
        repo.overwrite(mykeys, name="bob")

    with mock.patch("time.time", return_value=cur + 1):
        repo.overwrite(mykeys, recommend_server="ws://foo.com")

    assert repo.get(mykeys.public)["recommend_server"] == "ws://foo.com"


def test_overwrite_contact_list(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public, "", "")

    repo.overwrite(mykeys, contact_list=contact_list)

    assert repo.get(mykeys.public)["contacts"] == contact_list


def test_overwrite_contact_list_only_pubkey(mykeys, repo):
    contact1_keys = crypto.KeyPair()

    contact_list = contacts.ContactList()
    contact_list.add(contact1_keys.public)

    repo.overwrite(mykeys, contact_list=contact_list)

    assert repo.get(mykeys.public)["contacts"] == contact_list
