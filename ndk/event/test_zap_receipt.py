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

from ndk import types
from ndk.event import event_tags, zap_receipt_event


def test_init_bad_type(keys):
    with pytest.raises(ValueError, match="ZapReceiptEvent must have kind 9735"):
        zap_receipt_event.ZapReceiptEvent.build(
            keys, types.EventKind.SET_METADATA, content="foobar"
        )


def test_init_bad_content(keys):
    with pytest.raises(ValueError, match="ZapReceiptEvent must have empty content"):
        zap_receipt_event.ZapReceiptEvent.build(
            keys, types.EventKind.ZAP_RECEIPT, content="foobar"
        )


def test_init_no_p_tag(keys):
    tags = event_tags.EventTags()
    with pytest.raises(ValueError, match="ZapReceiptEvent must have a p tag"):
        zap_receipt_event.ZapReceiptEvent.build(
            keys, types.EventKind.ZAP_RECEIPT, tags=tags
        )


def test_init_no_bolt11_tag(keys):
    tags = event_tags.EventTags([["p", keys.public]])
    with pytest.raises(ValueError, match="ZapReceiptEvent must have a bolt11 tag"):
        zap_receipt_event.ZapReceiptEvent.build(
            keys, types.EventKind.ZAP_RECEIPT, tags=tags
        )


def test_init_no_description_tag(keys):
    tags = event_tags.EventTags([["p", keys.public], ["bolt11", "foobar"]])
    with pytest.raises(ValueError, match="ZapReceiptEvent must have a description tag"):
        zap_receipt_event.ZapReceiptEvent.build(
            keys, types.EventKind.ZAP_RECEIPT, tags=tags
        )


def test_correct(keys):
    tags = event_tags.EventTags(
        [["p", keys.public], ["bolt11", "foobar"], ["description", "barfoo"]]
    )
    zap_receipt_event.ZapReceiptEvent.build(
        keys, types.EventKind.ZAP_RECEIPT, tags=tags
    )
