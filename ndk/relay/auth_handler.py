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

import asyncio
import logging
import secrets
import typing
from urllib.parse import urlparse

from ndk import crypto
from ndk.event import auth_event
from ndk.messages import auth

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    if not url.startswith("wss://") and not url.startswith("ws://"):
        url = f"wss://{url}"
    return url


def relay_url_match(one, two) -> bool:
    if one == two:
        return True

    one = normalize_url(one)
    two = normalize_url(two)

    urlparsed_one = urlparse(one)
    urlparsed_two = urlparse(two)

    assert urlparsed_one.hostname
    assert urlparsed_two.hostname

    normalized_one = urlparsed_one.hostname.replace("www.", "")
    normalized_two = urlparsed_two.hostname.replace("www.", "")
    if normalized_one == normalized_two:
        return True

    return False


class AuthHandler:
    _authenticated: asyncio.Event
    _challenge: str
    _relay_url: str
    _authenticated_pubkey: typing.Optional[crypto.PublicKeyStr]

    def __init__(self, relay_url, allow_all=False):
        self._authenticated = asyncio.Event()
        if allow_all:
            self._authenticated.set()
        self._challenge = secrets.token_hex(16)
        self._relay_url = relay_url
        self._authenticated_pubkey = None

    def build_auth_message(self) -> str:
        return auth.AuthRequest(self._challenge).serialize()

    def handle_auth_event(self, ev: auth_event.AuthEvent):
        ev_relay_url = ev.tags.get("relay")
        if not relay_url_match(ev_relay_url[0][1], self._relay_url):
            raise ValueError(
                f"AuthEvent relay does not match expected relay: {self._relay_url} != {ev_relay_url}"
            )

        ev_challenge = ev.tags.get("challenge")
        if ev_challenge[0][1] != self._challenge:
            raise ValueError(
                f"AuthEvent challenge does not match expected challenge: {self._challenge} != {ev_challenge}"
            )

        self._authenticated_pubkey = ev.pubkey
        self._authenticated.set()

    def is_authenticated(self):
        return self._authenticated.is_set()

    async def wait_for_authenticated(self, timeout=1):
        try:
            await asyncio.wait_for(self._authenticated.wait(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise PermissionError("Authentication timed out") from exc

    def authenticated_pubkey(self) -> typing.Optional[crypto.PublicKeyStr]:
        return self._authenticated_pubkey
