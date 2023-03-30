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

from ndk import crypto, exceptions
from ndk.event import event, metadata_event


@pytest.fixture
def unsigned():
    return metadata_event.MetadataEvent.from_metadata_parts()


@pytest.fixture
def signed(unsigned):
    keys = crypto.KeyPair()
    return event.build_signed_event(unsigned, keys)


def test_signed_event_from_dict_bad_input():
    with pytest.raises(exceptions.ParseError):
        event.SignedEvent.from_dict({})


def test_signed_event_from_dict_bad_sig(signed):
    base_dict = signed.__dict__
    base_dict["sig"] = "badsig"

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_wrong_sig(signed):
    keys2 = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed2 = event.build_signed_event(unsigned, keys2)

    base_dict = signed.__dict__
    base_dict["sig"] = signed2.sig

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_wrong_id(signed):
    keys2 = crypto.KeyPair()
    unsigned = metadata_event.MetadataEvent.from_metadata_parts()
    signed2 = event.build_signed_event(unsigned, keys2)

    base_dict = signed.__dict__
    base_dict["id"] = signed2.id

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_ok(signed):
    event.SignedEvent.from_dict(signed.__dict__)


def test_from_dict_bad_id_errors(signed):
    d = signed.__dict__
    d["id"] = "uh oh"
    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(d)


def test_from_dict_invalid_id_errors(signed):
    d = signed.__dict__
    d["kind"] = event.EventKind.INVALID
    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(d)


def test_unsigned_from_signed(unsigned, signed):
    unsigned2 = metadata_event.MetadataEvent.from_signed_event(signed)

    assert unsigned == unsigned2


def test_from_validated_dict_correct(signed):
    signed2 = event.SignedEvent.from_validated_dict(signed.__dict__)
    assert signed == signed2


def test_from_validated_dict_bad_no_error(signed):
    d = signed.__dict__
    d["id"] = "uh oh"
    event.SignedEvent.from_validated_dict(d)
