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

import pytest

from ndk import crypto, exceptions, types
from ndk.event import event, event_builder, metadata_event
from ndk.event import parameterized_replaceable_event as pre


@pytest.fixture
def metadata_ev():
    return metadata_event.MetadataEvent.from_metadata_parts(crypto.KeyPair())


def test_event_from_dict_bad_input():
    with pytest.raises(ValueError):
        event_builder.from_dict({})


def test_event_from_dict_bad_pubkey(metadata_ev):
    base_dict = metadata_ev.__dict__
    base_dict["pubkey"] = "badpubkey"

    with pytest.raises(ValueError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_malformed_sig(metadata_ev):
    base_dict = metadata_ev.__dict__
    base_dict["sig"] = "badsig"

    with pytest.raises(ValueError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_formed_bad_sig(metadata_ev):
    base_dict = metadata_ev.__dict__
    base_dict["sig"] = "a" * 128

    with pytest.raises(ValueError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_malformed_id(metadata_ev):
    base_dict = metadata_ev.__dict__
    base_dict["id"] = "a" * 63

    with pytest.raises(ValueError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_wrong_sig(metadata_ev):
    event2 = metadata_event.MetadataEvent.from_metadata_parts(crypto.KeyPair())

    base_dict = metadata_ev.__dict__
    base_dict["sig"] = event2.sig

    with pytest.raises(exceptions.ValidationError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_wrong_id(metadata_ev):
    event2 = metadata_event.MetadataEvent.from_metadata_parts(crypto.KeyPair())

    base_dict = metadata_ev.__dict__
    base_dict["id"] = event2.id

    with pytest.raises(exceptions.ValidationError):
        event_builder.from_dict(base_dict)


def test_event_from_dict_ok(metadata_ev):
    event_builder.from_dict(metadata_ev.__dict__)


def test_from_dict_id_sig_mismatch(metadata_ev):
    d = metadata_ev.__dict__
    d["id"] = "a" * 64
    with pytest.raises(exceptions.ValidationError):
        event_builder.from_dict(d)


def test_from_dict_invalid_id_errors(metadata_ev):
    d = metadata_ev.__dict__
    d["kind"] = types.EventKind.INVALID
    with pytest.raises(ValueError):
        event_builder.from_dict(d)


def test_from_validated_dict_correct(metadata_ev):
    event2 = event_builder.from_validated_dict(metadata_ev.__dict__)
    assert metadata_ev == event2


def test_from_validated_dict_bad_no_error(metadata_ev):
    d = metadata_ev.__dict__
    d["id"] = "a" * 64
    event_builder.from_validated_dict(d)


def test_non_nip_regular_event():
    ev = event.Event.build(
        keys=crypto.KeyPair(),
        kind=1000,
        content="special state",
    )

    reconstructed_event = event_builder.from_dict(ev.__dict__)
    assert isinstance(reconstructed_event, event.RegularEvent)


def test_replaceable_event():
    ev = event.Event.build(
        keys=crypto.KeyPair(),
        kind=10000,
        content="special state",
    )

    reconstructed_event = event_builder.from_dict(ev.__dict__)
    assert isinstance(reconstructed_event, event.ReplaceableEvent)


def test_ephemeral_event():
    ev = event.Event.build(
        keys=crypto.KeyPair(),
        kind=20000,
        content="special state",
    )

    reconstructed_event = event_builder.from_dict(ev.__dict__)
    assert isinstance(reconstructed_event, event.EphemeralEvent)


def test_parameterized_replaceable_event():
    ev = event.Event.build(
        keys=crypto.KeyPair(),
        kind=30000,
        content="special state",
    )

    reconstructed_event = event_builder.from_dict(ev.__dict__)
    assert isinstance(reconstructed_event, pre.ParameterizedReplaceableEvent)
