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

import abc
import dataclasses
import typing


def is_instance_of_type(x, t):
    origin = typing.get_origin(t)
    if origin is None:
        return isinstance(x, t)
    else:
        args = typing.get_args(t)
        return (
            isinstance(x, origin)
            and all(isinstance(arg, type) for arg in args)
            and all(isinstance(item, args[0]) for item in x)
        )


@dataclasses.dataclass
class Message(abc.ABC):
    def __post_init__(self):
        for field in self.__annotations__:
            if not is_instance_of_type(
                getattr(self, field), self.__annotations__[field]
            ):
                raise TypeError(
                    f"Type mismatch for field {field}. {type(getattr(self, field))} != {self.__annotations__[field]}"
                )


@dataclasses.dataclass
class ReadableMessage(Message, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def deserialize_list(cls, lst: list) -> list:
        pass


@dataclasses.dataclass
class WriteableMessage(Message, abc.ABC):
    @abc.abstractmethod
    def serialize(self) -> str:
        pass
