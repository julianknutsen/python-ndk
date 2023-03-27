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

from ndk import crypto, exceptions
from ndk.event import event


def test_signed_event_from_dict_bad_input():
    with pytest.raises(exceptions.ParseError):
        event.SignedEvent.from_dict({})


def test_signed_event_from_dict_bad_sig():
    keys = crypto.KeyPair()
    unsigned = event.UnsignedEvent()
    signed = event.build_signed_event(unsigned, keys)

    base_dict = signed.__dict__
    base_dict["sig"] = "badsig"

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_wrong_sig():
    keys = crypto.KeyPair()
    keys2 = crypto.KeyPair()
    unsigned = event.UnsignedEvent()
    signed = event.build_signed_event(unsigned, keys)
    signed2 = event.build_signed_event(unsigned, keys2)

    base_dict = signed.__dict__
    base_dict["sig"] = signed2.sig

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_wrong_id():
    keys = crypto.KeyPair()
    keys2 = crypto.KeyPair()
    unsigned = event.UnsignedEvent()
    signed = event.build_signed_event(unsigned, keys)
    signed2 = event.build_signed_event(unsigned, keys2)

    base_dict = signed.__dict__
    base_dict["id"] = signed2.id

    with pytest.raises(event.ValidationError):
        event.SignedEvent.from_dict(base_dict)


def test_signed_event_from_dict_ok():
    keys = crypto.KeyPair()
    unsigned = event.UnsignedEvent()
    signed = event.build_signed_event(unsigned, keys)

    event.SignedEvent.from_dict(signed.__dict__)


def test_unsigned_from_signed():
    keys = crypto.KeyPair()
    unsigned = event.UnsignedEvent()
    signed = event.build_signed_event(unsigned, keys)

    unsigned2 = event.UnsignedEvent.from_signed_event(signed)

    assert unsigned == unsigned2
