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

import pytest

from ndk import crypto, types
from ndk.event import event_tags

VALID_PUBKEY_STR = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
VALID_EVENT_ID_STR = VALID_PUBKEY_STR
VALID_RELAY_STR = "wss://nostr.com.se"


def test_init_event_tag_bad_type_fails():
    with pytest.raises(ValueError):
        event_tags.EventTag("")  # type: ignore


def test_init_event_tag_no_content():
    with pytest.raises(ValueError):
        event_tags.EventTag([])


def test_init_event_tag_one_item():
    with pytest.raises(ValueError):
        event_tags.EventTag(["p"])


def test_init_event_tag_bad_type():
    with pytest.raises(ValueError):
        event_tags.EventTag(["p", 1])  # type: ignore


def test_init_p_tag_bad_length():
    with pytest.raises(ValueError):
        event_tags.PublicKeyTag(["p", VALID_PUBKEY_STR, "b", "c"])


def test_init_p_tag_bad_start():
    with pytest.raises(ValueError):
        event_tags.PublicKeyTag(["e", "b"])


def test_init_p_tag_str():
    et = event_tags.PublicKeyTag(["p", VALID_PUBKEY_STR])
    assert str(et) == f"['p', '{VALID_PUBKEY_STR}']"


def test_init_p_tag_cryptopubkey():
    et = event_tags.PublicKeyTag(["p", crypto.PublicKeyStr(VALID_PUBKEY_STR)])
    assert str(et) == f"['p', '{VALID_PUBKEY_STR}']"


def test_init_p_tag_from_pubkey_str():
    event_tags.PublicKeyTag.from_pubkey(VALID_PUBKEY_STR)  # type: ignore


def test_init_p_tag_from_pubkey():
    et = event_tags.PublicKeyTag.from_pubkey(crypto.PublicKeyStr(VALID_PUBKEY_STR))
    assert str(et) == f"['p', '{VALID_PUBKEY_STR}']"


def test_init_p_tag_from_pubkey_with_relay():
    et = event_tags.PublicKeyTag.from_pubkey(
        crypto.PublicKeyStr(VALID_PUBKEY_STR), VALID_RELAY_STR
    )
    assert str(et) == f"['p', '{VALID_PUBKEY_STR}', '{VALID_RELAY_STR}']"


def test_init_p_tag_from_pubkey_with_malformed_relay():
    with pytest.raises(ValueError):
        event_tags.PublicKeyTag.from_pubkey(
            crypto.PublicKeyStr(VALID_PUBKEY_STR), "blah"
        )


def test_init_e_tag_bad_length():
    with pytest.raises(ValueError):
        event_tags.EventIdTag(["e", VALID_EVENT_ID_STR, "b", "g"])


def test_init_e_tag_bad_start():
    with pytest.raises(ValueError):
        event_tags.EventIdTag(["p", VALID_EVENT_ID_STR])


def test_init_e_tag_event_id_str():
    et = event_tags.EventIdTag(["e", VALID_EVENT_ID_STR])
    assert str(et) == f"['e', '{VALID_EVENT_ID_STR}']"


def test_init_e_tag_event_id():
    et = event_tags.EventIdTag(["e", types.EventID(VALID_EVENT_ID_STR)])
    assert str(et) == f"['e', '{VALID_EVENT_ID_STR}']"


def test_init_e_tag_from_event_id_str():
    et = event_tags.EventIdTag.from_event_id(VALID_EVENT_ID_STR)  # type: ignore
    assert str(et) == f"['e', '{VALID_EVENT_ID_STR}']"


def test_init_e_tag_from_pubkey():
    et = event_tags.EventIdTag.from_event_id(types.EventID(VALID_EVENT_ID_STR))
    assert str(et) == f"['e', '{VALID_EVENT_ID_STR}']"


def test_init_e_tag_from_pubkey_and_relay():
    et = event_tags.EventIdTag.from_event_id(
        types.EventID(VALID_EVENT_ID_STR), VALID_RELAY_STR
    )
    assert str(et) == f"['e', '{VALID_EVENT_ID_STR}', '{VALID_RELAY_STR}']"


def test_init_e_tag_from_pubkey_and_malformed_relay():
    with pytest.raises(ValueError):
        event_tags.EventIdTag.from_event_id(types.EventID(VALID_EVENT_ID_STR), "blergh")


def test_unknown_event_tag():
    et = event_tags.UnknownEventTag(["u", "a"])
    assert str(et) == "['u', 'a']"


def test_event_tags_bad_type():
    with pytest.raises(ValueError):
        event_tags.EventTags("")  # type: ignore


def test_event_tags_bady_type_in_list():
    with pytest.raises(ValueError):
        event_tags.EventTags([["p", VALID_PUBKEY_STR], 1])  # type: ignore


def test_event_tags_malformed_list():
    with pytest.raises(ValueError):
        event_tags.EventTags([["e"]])


def test_event_tags():
    et = event_tags.EventTags([["p", VALID_PUBKEY_STR]])
    assert str(et) == f"[['p', '{VALID_PUBKEY_STR}']]"


def test_event_tags_multiple_output_same_order():
    et = event_tags.EventTags(
        [["p", VALID_PUBKEY_STR], ["e", VALID_EVENT_ID_STR], ["r", "r"]]
    )
    assert (
        str(et)
        == f"[['p', '{VALID_PUBKEY_STR}'], ['e', '{VALID_EVENT_ID_STR}'], ['r', 'r']]"
    )


def test_event_tags_add_one():
    et = event_tags.EventTags()
    et.add(event_tags.PublicKeyTag.from_pubkey(VALID_PUBKEY_STR))
    assert str(et) == f"[['p', '{VALID_PUBKEY_STR}']]"


def test_event_tags_add_multiple_maintain_order():
    et = event_tags.EventTags()
    et.add(event_tags.PublicKeyTag.from_pubkey(VALID_PUBKEY_STR))
    et.add(event_tags.EventIdTag.from_event_id(VALID_EVENT_ID_STR))
    assert str(et) == f"[['p', '{VALID_PUBKEY_STR}'], ['e', '{VALID_EVENT_ID_STR}']]"


def test_event_tags_get_nothing():
    et = event_tags.EventTags()
    assert et.get("p") == []


def test_event_tags_add_get():
    et = event_tags.EventTags()
    et.add(event_tags.PublicKeyTag.from_pubkey(VALID_PUBKEY_STR))
    assert len(et.get("p")) == 1
