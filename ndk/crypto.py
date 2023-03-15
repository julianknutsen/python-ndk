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

"""Crypto utility functions and types to handle all keys & encryption

This module exists to abstract the cryptography from the business layers. Simple
wrapper types have been created to make it harder to do the wrong thing passing
around bytes & strings.

For cross-platform usage, this leverages the coincurve library.

Example::

    keys = Keypair()
    human_readable_pubkey: PublicKeyStr = keys.public
    sig = keys.private.sign_schnorr(payload)
"""

import typing

import coincurve

SchnorrSigStr = typing.NewType("SchnorrSigStr", str)
PublicKeyStr = typing.NewType("PublicKeyStr", str)


class PrivateKey:
    """Private key for use with signing, encryption, decryption

    Attributes:
        None
    """

    _raw: coincurve.PrivateKey

    def __init__(self):
        """Initializes a new PrivateKey"""
        self._raw = coincurve.PrivateKey()

    def calculate_public_key(self) -> PublicKeyStr:
        """Calculate the corresponding Public Key

        For compatibility with BIP340, the first byte is dropped from the standard
        compressed public key https://bips.xyz/340#public-key-conversion.

        Returns:
            A 32-byte human-readable, lowercase, hex string encapsulated in a
            PublicKeyStr type
        """
        pub = coincurve.PublicKey.from_secret(self._raw.secret)
        return PublicKeyStr(pub.format(compressed=True).hex().lower()[2:])

    def sign_schnorr(self, payload: bytes) -> SchnorrSigStr:
        """Generate a Schnorr signature for a given payload

        Returns:
            A human-readable hex string of the signature

        Raises:
            ValueError: If the payload was not 32 bytes or the underlying signing failed
        """

        return SchnorrSigStr(self._raw.sign_schnorr(payload).hex())


class KeyPair:
    """Private/Public KeyPair"""

    public: PublicKeyStr
    private: PrivateKey

    def __init__(self):
        """Initializes a new Public/Private pair"""
        self.private = PrivateKey()
        self.public = self.private.calculate_public_key()
