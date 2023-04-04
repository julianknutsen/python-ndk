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

# https://github.com/nostr-protocol/nips/blob/master/11.md
# {
#   "name": <string identifying relay>,
#   "description": <string with detailed information>,
#   "pubkey": <administrative contact pubkey>,
#   "contact": <administrative alternate contact>,
#   "supported_nips": <a list of NIP numbers supported by the relay>,
#   "software": <string identifying relay software URL>,
#   "version": <string version identifier>
# }

import dataclasses
import typing

from ndk import serialize


@dataclasses.dataclass
class RelayInformationDocument:
    name: typing.Optional[str] = None
    description: typing.Optional[str] = None
    pubkey: typing.Optional[str] = None
    contact: typing.Optional[str] = None
    supported_nips: typing.Optional[list[int]] = None
    software: typing.Optional[str] = None
    version: typing.Optional[str] = None

    def serialize_as_bytes(self) -> bytes:
        return serialize.serialize_as_bytes(
            {k: v for k, v in self.__dict__.items() if v is not None}
        )

    @classmethod
    def from_json(cls, json: str):
        obj = serialize.deserialize(json)
        if not isinstance(obj, dict):
            raise ValueError("Invalid JSON")
        return cls(**obj)
