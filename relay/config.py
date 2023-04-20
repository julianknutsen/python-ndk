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

import configparser
import dataclasses

from ndk import serialize


@dataclasses.dataclass
class GeneralConfig:
    name: str
    description: str
    software: str
    supported_nips: list[int]
    version: str

    @classmethod
    def from_config(cls, cfg: configparser.ConfigParser):
        return cls(
            name=cfg.get("General", "name", fallback="Default Relay from python-ndk"),
            description=cfg.get(
                "General",
                "description",
                fallback="Production instance running at wss://nostr.com.se",
            ),
            software=cfg.get(
                "General",
                "software",
                fallback="git+https://github.com/julianknutsen/python-ndk",
            ),
            supported_nips=serialize.deserialize_str(
                cfg.get(
                    "General",
                    "supported_nips",
                    fallback="[1, 2, 10, 11, 13, 15, 16, 18, 20, 25, 33, 57]",
                )
            ),
            version=cfg.get("General", "version", fallback="0.1"),
        )

    def to_rid_section(self) -> dict:
        return self.__dict__


@dataclasses.dataclass
class LimitationsConfig:
    max_message_length: int
    max_subscriptions: int
    max_filters: int
    max_limit: int
    max_subid_length: int
    min_prefix: int
    max_event_tags: int
    max_content_length: int
    auth_required: bool
    payment_required: bool

    @classmethod
    def from_config(cls, cfg: configparser.ConfigParser):
        return cls(
            max_message_length=cfg.getint(
                "Limitation", "max_message_length", fallback=16384
            ),
            max_subscriptions=cfg.getint(
                "Limitation", "max_subscriptions", fallback=20
            ),
            max_filters=cfg.getint("Limitation", "max_filters", fallback=100),
            max_limit=cfg.getint("Limitation", "max_limit", fallback=5000),
            max_subid_length=cfg.getint("Limitation", "max_subid_length", fallback=100),
            min_prefix=cfg.getint("Limitation", "min_prefix", fallback=4),
            max_event_tags=cfg.getint("Limitation", "max_event_tags", fallback=100),
            max_content_length=cfg.getint(
                "Limitation", "max_content_length", fallback=8196
            ),
            auth_required=cfg.getboolean("Limitation", "auth_required", fallback=False),
            payment_required=cfg.getboolean(
                "Limitation", "payment_required", fallback=False
            ),
        )

    def to_rid_section(self) -> dict:
        return self.__dict__


class RelayConfig:
    general: GeneralConfig
    limitations: LimitationsConfig

    def __init__(self, cfg: configparser.ConfigParser):
        self.general = GeneralConfig.from_config(cfg)
        self.limitations = LimitationsConfig.from_config(cfg)

    def to_rid(self) -> dict:
        ret = self.general.to_rid_section()
        ret["limitation"] = self.limitations.to_rid_section()

        return ret
