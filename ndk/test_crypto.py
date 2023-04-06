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

from ndk import crypto


def test_public_key_creation():
    keys = crypto.KeyPair()
    assert len(keys.public) == 64


def test_sign_verify():
    keys = crypto.KeyPair()
    message = "00112233445566778899aabbccddeeff".encode()

    sig = keys.private.sign_schnorr(message)

    assert crypto.verify_signature(keys.public, sig, message)


def test_sign_verify_bad():
    keys1 = crypto.KeyPair()
    keys2 = crypto.KeyPair()
    message = "00112233445566778899aabbccddeeff".encode()

    sig = keys1.private.sign_schnorr(message)

    assert not crypto.verify_signature(keys2.public, sig, message)


def test_schnorrsigstr_bad_size():
    with pytest.raises(ValueError):
        crypto.SchnorrSigStr("a" * 127)


def test_schnorrsigstr_non_hex():
    with pytest.raises(ValueError):
        crypto.SchnorrSigStr("$" * 128)


def test_publickeystr_bad_size():
    with pytest.raises(ValueError):
        crypto.PublicKeyStr("a" * 63)


def test_publickeystr_non_hex():
    with pytest.raises(ValueError):
        crypto.PublicKeyStr("$" * 64)
