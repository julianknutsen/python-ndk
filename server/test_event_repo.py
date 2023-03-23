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

from ndk import crypto
from ndk.event import event, metadata_event
from server import event_repo


def test_get_empty():
    repo = event_repo.EventRepo()
    items = repo.get([{}])

    assert len(items) == 0


def test_get_matches_by_id():
    repo = event_repo.EventRepo()

    keys = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(unsigned, keys)

    ev_id = repo.add(signed)

    items = repo.get([{"ids": [ev_id]}])

    assert len(items) == 1
    assert items[0] == signed


def test_get_matches_by_author():
    repo = event_repo.EventRepo()

    keys = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(unsigned, keys)

    _ = repo.add(signed)

    items = repo.get([{"authors": [keys.public]}])

    assert len(items) == 1
    assert items[0] == signed


def test_get_matches_by_author_and_id():
    repo = event_repo.EventRepo()

    keys = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(unsigned, keys)

    ev_id = repo.add(signed)

    items = repo.get([{"ids": [ev_id], "authors": [keys.public]}])

    assert len(items) == 1
    assert items[0] == signed


def test_get_matches_by_id_only_last():
    repo = event_repo.EventRepo()

    keys = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(unsigned, keys)
    signed2 = event.build_signed_event(unsigned, keys)

    _ = repo.add(signed)
    _ = repo.add(signed2)

    items = repo.get([{"authors": [keys.public], "limit": 1}])

    assert len(items) == 1
    assert items[0] == signed2


def test_get_matches_by_id_limit_greater():
    repo = event_repo.EventRepo()

    keys = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed = event.build_signed_event(unsigned, keys)

    _ = repo.add(signed)

    items = repo.get([{"authors": [keys.public], "limit": 2}])

    assert len(items) == 1
    assert items[0] == signed
