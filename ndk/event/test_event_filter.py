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

from ndk.event import event_filter


def test_init():
    event_filter.EventFilter()


@pytest.mark.parametrize("ids", ["1", [1]])
def test_init_bad_type_ids(ids):
    with pytest.raises(ValueError):
        event_filter.EventFilter(ids=ids)  # type: ignore


@pytest.mark.parametrize("authors", ["1", [1]])
def test_init_bad_type_authors(authors):
    with pytest.raises(ValueError):
        event_filter.EventFilter(authors=authors)  # type: ignore


@pytest.mark.parametrize("kinds", ["1", ["1"]])
def test_init_bad_type_kinds(kinds):
    with pytest.raises(ValueError):
        event_filter.EventFilter(kinds=kinds)  # type: ignore


@pytest.mark.parametrize("e_tags", ["1", [1]])
def test_init_bad_type_e_tags(e_tags):
    with pytest.raises(ValueError):
        event_filter.EventFilter(e_tags=e_tags)  # type: ignore


@pytest.mark.parametrize("p_tags", ["1", [1]])
def test_init_bad_type_p_tags(p_tags):
    with pytest.raises(ValueError):
        event_filter.EventFilter(p_tags=p_tags)  # type: ignore


@pytest.mark.parametrize("since", [-1, "1"])
def test_init_bad_type_since(since):
    with pytest.raises(ValueError):
        event_filter.EventFilter(since=since)  # type: ignore


@pytest.mark.parametrize("until", [-1, "1"])
def test_init_bad_type_until(until):
    with pytest.raises(ValueError):
        event_filter.EventFilter(until=until)  # type: ignore


@pytest.mark.parametrize("limit", [-1, "1"])
def test_init_bad_type_limit_zero(limit):
    with pytest.raises(ValueError):
        event_filter.EventFilter(limit=limit)


def test_empty_matches_all():
    f = event_filter.EventFilter()

    mock_ev = mock.MagicMock()
    assert f.matches_event(mock_ev)


def test_matches_event_id_empty_list_matches_all():
    f = event_filter.EventFilter(ids=[])

    mock_ev = mock.MagicMock()
    mock_ev.id = "eventid"
    assert f.matches_event(mock_ev)

    mock_ev.id = "othereventid"
    assert f.matches_event(mock_ev)


def test_matches_event_id():
    f = event_filter.EventFilter(ids=["eventid"])

    mock_ev = mock.MagicMock()
    mock_ev.id = "eventid"
    assert f.matches_event(mock_ev)

    mock_ev.id = "othereventid"
    assert not f.matches_event(mock_ev)


def test_matches_event_id_many():
    f = event_filter.EventFilter(ids=["eventid", "othereventid"])

    mock_ev = mock.MagicMock()
    mock_ev.id = "eventid"
    assert f.matches_event(mock_ev)

    mock_ev.id = "othereventid"
    assert f.matches_event(mock_ev)

    mock_ev.id = "otherothereventid"
    assert not f.matches_event(mock_ev)


def test_matches_event_authors_empty_list_matches_all():
    f = event_filter.EventFilter(authors=[])

    mock_ev = mock.MagicMock()
    mock_ev.pubkey = "match"
    assert f.matches_event(mock_ev)

    mock_ev.pubkey = "notmatch"
    assert f.matches_event(mock_ev)


def test_matches_event_authors():
    f = event_filter.EventFilter(authors=["match"])

    mock_ev = mock.MagicMock()
    mock_ev.pubkey = "match"
    assert f.matches_event(mock_ev)

    mock_ev.pubkey = "notmatch"
    assert not f.matches_event(mock_ev)


def test_matches_event_authors_many():
    f = event_filter.EventFilter(authors=["match", "match2"])

    mock_ev = mock.MagicMock()
    mock_ev.pubkey = "match"
    assert f.matches_event(mock_ev)

    mock_ev.pubkey = "match2"
    assert f.matches_event(mock_ev)

    mock_ev.pubkey = "notmatch"
    assert not f.matches_event(mock_ev)


def test_matches_event_kinds_empty_list_matches_all():
    f = event_filter.EventFilter(kinds=[])

    mock_ev = mock.MagicMock()
    mock_ev.kind = 1
    assert f.matches_event(mock_ev)

    mock_ev.kind = 2
    assert f.matches_event(mock_ev)


def test_matches_event_kinds_zero_matches_0():
    f = event_filter.EventFilter(kinds=[0])

    mock_ev = mock.MagicMock()
    mock_ev.kind = 0
    assert f.matches_event(mock_ev)

    mock_ev.kind = 1
    assert not f.matches_event(mock_ev)


def test_matches_event_kinds():
    f = event_filter.EventFilter(kinds=[1])

    mock_ev = mock.MagicMock()
    mock_ev.kind = 1
    assert f.matches_event(mock_ev)

    mock_ev.kind = 2
    assert not f.matches_event(mock_ev)


def test_matches_event_kinds_many():
    f = event_filter.EventFilter(kinds=[1, 2])

    mock_ev = mock.MagicMock()
    mock_ev.kind = 1
    assert f.matches_event(mock_ev)

    mock_ev.kind = 2
    assert f.matches_event(mock_ev)

    mock_ev.kind = 3
    assert not f.matches_event(mock_ev)


def test_matches_event_tags_empty_list_matches_all():
    f = event_filter.EventFilter(e_tags=[])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["e", "eventid"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["e", "othereventid"]]
    assert f.matches_event(mock_ev)


def test_matches_event_tags():
    f = event_filter.EventFilter(e_tags=["eventid"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["e", "eventid"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["e", "othereventid"]]
    assert not f.matches_event(mock_ev)

    mock_ev.tags = [["p", "pubkey"]]
    assert not f.matches_event(mock_ev)


def test_matches_event_tags_many():
    f = event_filter.EventFilter(e_tags=["eventid", "eventid2"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["e", "eventid"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["e", "eventid2"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["e", "othereventid"]]
    assert not f.matches_event(mock_ev)


def test_matches_event_tags_many_in_event():
    f = event_filter.EventFilter(e_tags=["eventid"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["e", "eventid"], ["e", "eventid2"]]
    assert f.matches_event(mock_ev)

    f = event_filter.EventFilter(e_tags=["eventid2"])
    assert f.matches_event(mock_ev)


def test_matches_event_tags_unknown_identifier_ignored():
    f = event_filter.EventFilter(e_tags=["eventid"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["e", "eventid"], ["f", "unknown tag"]]
    assert f.matches_event(mock_ev)


def test_matches_pubkey_tags_empty_list_matches_all():
    f = event_filter.EventFilter(p_tags=["matches"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["p", "matches"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["p", "notmatches"]]
    assert not f.matches_event(mock_ev)


def test_matches_pubkey_tags():
    f = event_filter.EventFilter(p_tags=["matches"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["p", "matches"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["p", "notmatches"]]
    assert not f.matches_event(mock_ev)

    mock_ev.tags = [["e", "othereventid"]]
    assert not f.matches_event(mock_ev)


def test_matches_pubkey_tags_many():
    f = event_filter.EventFilter(p_tags=["matches", "matches2"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["p", "matches"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["p", "matches2"]]
    assert f.matches_event(mock_ev)

    mock_ev.tags = [["p", "notmatches"]]
    assert not f.matches_event(mock_ev)


def test_matches_pubkey_tags_many_in_event():
    f = event_filter.EventFilter(p_tags=["matches"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["p", "matches"], ["p", "matches2"]]
    assert f.matches_event(mock_ev)

    f = event_filter.EventFilter(p_tags=["matches"])
    assert f.matches_event(mock_ev)

    f = event_filter.EventFilter(p_tags=["matches2"])
    assert f.matches_event(mock_ev)


def test_matches_event_and_pubkey_tags():
    f = event_filter.EventFilter(p_tags=["matches"], e_tags=["eventid"])

    mock_ev = mock.MagicMock()
    mock_ev.tags = [["p", "matches"]]
    assert not f.matches_event(mock_ev)

    mock_ev.tags = [["e", "eventid"]]
    assert not f.matches_event(mock_ev)

    mock_ev.tags = [["p", "matches"], ["e", "eventid"]]
    assert f.matches_event(mock_ev)


def test_matches_since_earlier():
    f = event_filter.EventFilter(since=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 0
    assert not f.matches_event(mock_ev)


def test_matches_since_equal():
    f = event_filter.EventFilter(since=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 1
    assert not f.matches_event(mock_ev)


def test_matches_since_later():
    f = event_filter.EventFilter(since=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 2
    assert f.matches_event(mock_ev)


def test_matches_until_earlier():
    f = event_filter.EventFilter(until=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 0
    assert f.matches_event(mock_ev)


def test_matches_until_equal():
    f = event_filter.EventFilter(until=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 1
    assert not f.matches_event(mock_ev)


def test_matches_until_later():
    f = event_filter.EventFilter(until=1)

    mock_ev = mock.MagicMock()
    mock_ev.created_at = 2
    assert not f.matches_event(mock_ev)


def test_to_req():
    f = event_filter.EventFilter(ids=["1", "2"])
    assert f.for_req() == {"ids": ["1", "2"]}


def test_to_req_tags():
    f = event_filter.EventFilter(
        e_tags=["eventid", "eventid2"], p_tags=["pubkey", "pubkey2"]
    )
    assert f.for_req() == {"#e": ["eventid", "eventid2"], "#p": ["pubkey", "pubkey2"]}


@pytest.mark.parametrize(
    "field, value",
    [
        ("ids", []),
        ("authors", []),
        ("kinds", []),
        ("e_tags", []),
        ("p_tags", []),
    ],
)
def test_to_req_empty_list_excluded(field, value):
    f = event_filter.EventFilter(**{field: value})
    assert not f.for_req()
