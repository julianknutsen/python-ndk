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
from ndk.repos.text_note_repo import event_backed_text_note_repo, fake_text_note_repo


@pytest.fixture
def fake():
    return fake_text_note_repo.FakeTextNoteRepo()


@pytest.fixture
def local(local_ev_repo):
    return event_backed_text_note_repo.EventBackedTextNoteRepo(local_ev_repo)


@pytest.fixture
def remote(remote_ev_repo):
    return event_backed_text_note_repo.EventBackedTextNoteRepo(remote_ev_repo)


@pytest.fixture(params=["fake", "local", "remote"])
def repo(request):
    return request.getfixturevalue(request.param)


async def test_set_retrieve(repo):
    mykeys = crypto.KeyPair()

    # send plaintext note
    info = await repo.add(mykeys, "plaintext content goes here!")

    # retrieve by id
    text_note = await repo.get_by_uid(info)

    # retrive by author
    text_notes = await repo.get_by_author(mykeys.public)

    assert text_note == "plaintext content goes here!"
    assert text_notes[0] == "plaintext content goes here!"
