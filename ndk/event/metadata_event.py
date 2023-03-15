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

import dataclasses
import typing

from ndk.event import event, serialize


@dataclasses.dataclass(frozen=True)
class MetadataEvent(event.UnsignedEvent):
    @classmethod
    def from_metadata_parts(
        cls,
        name: typing.Optional[str] = None,
        about: typing.Optional[str] = None,
        picture: typing.Optional[str] = None,
        **kwargs,
    ) -> "MetadataEvent":
        content = {**kwargs}
        if name:
            content["name"] = name

        if about:
            content["about"] = about

        if picture:
            content["picture"] = picture

        serialized_content = serialize.serialize_as_str(content)
        return cls(kind=event.EventKind.SET_METADATA, content=serialized_content)