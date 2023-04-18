![GitHub](https://img.shields.io/github/license/julianknutsen/python-ndk) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/julianknutsen/python-ndk/precommit.yaml) [![codecov](https://codecov.io/gh/julianknutsen/python-ndk/branch/main/graph/badge.svg?token=6T90F67SLC)](https://codecov.io/gh/julianknutsen/python-ndk)

# Introduction
Development library for the [Nostr](https://github.com/nostr-protocol/nostr) protocol. Full implementation of a server and partial implementation of client features already completed. Work is ongoing.

See the [issue tracker](https://github.com/julianknutsen/python-ndk/issues) more information.

Use the production instance at [wss://nostr.com.se](wss://nostr.com.se) or run your own instance.


# Server NIP Support
| NIP | Status               | Notes |
|-----|:--------:              |------|
| [NIP-01: Basic protocol flow description](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/01.md) | :white_check_mark: | |
| [NIP-02: Contact List and Petnames](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/02.md) | :white_check_mark:  | |
| [NIP-03: OpenTimestamps Attestations for Events](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/03.md) | :x: | Backlog |
| [NIP-04: Encrypted Direct Message](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/04.md) | :white_check_mark: | Storage by anyone, AUTH for retrieval |
| [NIP-09: Event Deletion](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/09.md) | :white_check_mark: | Backlog (may not support) |
| [NIP-10: Conventions for clients' use of e and p tags in text events](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/10.md) |:white_check_mark: | Supports marker field in e tag |
| [NIP-11: Relay Information Document](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/11.md) | :white_check_mark: | See config.ini for specific config features |
| [NIP-12: Generic Tag Queries](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/12.md) | :white_check_mark: | |
| [NIP-13: Proof of Work](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/13.md) | :x: | [Backlog](https://github.com/julianknutsen/python-ndk/issues/73) |
| [NIP-16: Event Treatment](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/16.md) | :white_check_mark: | |
| [NIP-20: Command Results](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/20.md) | :white_check_mark: | |
| [NIP-22: Event created_at Limits](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/22.md) | :x: | Backlog |
| [NIP-25: Reactions](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/25.md) | :white_check_mark: | Validation of event format |
| [NIP-26: Delegated Event Signing](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/26.md) | :x: | Backlog |
| [NIP-28: Public Chat](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/26.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-33: Parameterized Replaceable Events](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/33.md) | :white_check_mark: | |
| [NIP-40: Expiration Timestamp](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/40.md) | :x: | May not implement for same reason as delete |
| [NIP-42: Authentication of clients to relays](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/42.md) |:white_check_mark: | |
| [NIP-45: Counting results](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/45.md) | :x: | Backlog |
| [NIP-46: Nostr Connect](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/46.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-50: Keywords filter](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/50.md) | :x: | Backlog |
| [NIP-51: Lists](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/51.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-56: Reporting](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/56.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-57: Lightning Zaps](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/57.md) | :white_check_mark: | Zap Receipt format validated |
| [NIP-58: Badges](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/58.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-65: Relay List Metadata](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/65.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |
| [NIP-78: Application-specific data](https://github.com/nostr-protocol/nips/blob/127d5518bfa9a4e4e7510490c0b8d95e342dfa4b/78.md) | :warning: | Event can be saved/retrieved, but format is not validated, yet |