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

from ndk.relay import relay_information_document


def test_init():
    relay_information_document.RelayInformationDocument()


def test_bad_json():
    with pytest.raises(ValueError):
        relay_information_document.RelayInformationDocument.from_json("[]")


def test_good_json():
    relay_information_document.RelayInformationDocument.from_json("{}")


def test_serialize():
    assert (
        b"{}"
        == relay_information_document.RelayInformationDocument(
            name=None
        ).serialize_as_bytes()
    )


def test_empty_removed():
    assert (
        b"{}"
        == relay_information_document.RelayInformationDocument().serialize_as_bytes()
    )


def test_limitation():
    assert (
        b'{"limitation":{"auth_required":false}}'
        == relay_information_document.RelayInformationDocument(
            limitation_auth_required=False
        ).serialize_as_bytes()
    )


def test_two_limitation():
    assert (
        b'{"limitation":{"auth_required":false,"payment_required":false}}'
        == relay_information_document.RelayInformationDocument(
            limitation_auth_required=False, limitation_payment_required=False
        ).serialize_as_bytes()
    )


def test_general_and_limitation():
    assert (
        b'{"limitation":{"auth_required":false},"name":"foo"}'
        == relay_information_document.RelayInformationDocument(
            name="foo", limitation_auth_required=False
        ).serialize_as_bytes()
    )
