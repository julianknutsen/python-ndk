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

import secrets

from ndk.event import auth_event
from ndk.messages import auth


class AuthHandler:
    _authenticated: bool
    _challenge: str
    _relay_url: str

    def __init__(self, relay_url):
        self._authenticated = False
        self._challenge = secrets.token_hex(16)
        self._relay_url = relay_url

    def build_auth_message(self) -> str:
        return auth.Auth(self._challenge).serialize()

    def handle_auth_event(self, ev: auth_event.AuthEvent):
        ev_relay_url = ev.tags.get("relay")
        if ev_relay_url[0][1] != self._relay_url:
            raise ValueError(
                f"AuthEvent relay does not match expected relay: {self._relay_url} != {ev_relay_url}"
            )

        ev_challenge = ev.tags.get("challenge")
        if ev_challenge[0][1] != self._challenge:
            raise ValueError(
                f"AuthEvent challenge does not match expected challenge: {self._challenge} != {ev_challenge}"
            )

        self._authenticated = True

    def is_authenticated(self):
        return self._authenticated
