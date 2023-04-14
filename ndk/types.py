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


class FixedLengthHexStr(str):
    _length: int

    def __new__(cls, value: str):
        cls.validate(value)

        return super().__new__(cls, value)

    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise ValueError(f"{cls.__name__} must be a string, not {type(value)}")

        if len(value) != cls._length:
            raise ValueError(
                f"{cls.__name__} must be {cls._length} bytes long, not {value}"
            )

        if not all(c in "0123456789abcdef" for c in value):
            raise ValueError(f"{cls.__name__} must be a hex string, not {value}")


class EventID(FixedLengthHexStr):
    _length: int = 64


class EventKind:
    INVALID = -1
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_SERVER = 2
    CONTACT_LIST = 3
    REPOST = 6
    REACTION = 7
