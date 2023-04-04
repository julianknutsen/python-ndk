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

# pylint: disable=redefined-outer-name, unused-argument

import warnings

import pytest
import requests

from ndk import serialize


@pytest.fixture
def response(relay_url):
    url = relay_url.replace("wss://", "https://")
    response = requests.get(
        url, headers={"Accept": "application/nostr+json"}, timeout=10, verify=False
    )

    if response.status_code != 200:
        warnings.warn(f"Got {response.status_code} from {url}")
    else:
        return serialize.deserialize(response.content.decode())


def test_basic(response):
    pass  # test in fixture


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "description",
        "pubkey",
        "contact",
        "supported_nips",
        "software",
        "version",
        "foobar",
    ],
)
def test_has_known_fields(field, response):
    if field not in response:
        warnings.warn(f"No '{field}' field in response")
