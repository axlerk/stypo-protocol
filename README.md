# Stypo Wire-Format Specification

<!-- public-mirror-banner -->

> **Public mirror.** This repository is automatically synchronised from
> the `spec/` directory of the (private) Stypo source tree. Filing
> issues against the spec here is fine; canonical edits happen upstream
> and propagate on every push to Stypo's `main`.

**Status:** draft, public for review (first written 2026-11-08). `open-v1`
and `stealth-v1` are what the app writes and reads; three constants are
still open (see "What is measured and what may change").

This directory is the normative specification of the formats Stypo hides
inside an ordinary text message. It exists so that anyone can:

1. Read the spec and see what is on the wire.
2. Run the reference decoder (`reference/python/`) on a real message.
3. Compare the result against the test vectors (`test-vectors/`).

If the app does anything different from what is written here, one of the two
has a bug: please report it (below).

**Stypo is the easiest member of its family to detect.** The hidden stream
is a run of invisible characters that a one-line scan finds. Stealth mode
hides what a message says, not that it is there
([`THREAT_MODEL.md`](THREAT_MODEL.md), §3.1).

## Layout

| File | What it covers |
|------|----------------|
| [`text-layer.md`](text-layer.md) | Bytes as variation selectors; how a decoder finds the run; where an encoder places it; the size boundary and the cap; decoder results. Shared by both modes. |
| [`open-v1.md`](open-v1.md) | Open mode: public, no privacy, and it names the app on purpose. |
| [`stealth-v1.md`](stealth-v1.md) | Stealth mode: framing and cryptography. The mode that protects messages. |
| [`reference/python/`](reference/python/) | Reference decoder, the vector emitter and the checker. |
| [`test-vectors/`](test-vectors/) | Messages, passwords and the expected results. |

## What is measured and what may change

**Measured:** Messages draws a text bubble whole up to 4 000 UTF-16 units
and collapses a longer one (iOS 26.7.2, 27.0 in the simulator, 27.2), and
the run arrived unchanged through iMessage between two iPhones. The details
are in `text-layer.md` §6 and in the threat model (§3.4).

**Decided:** the cap of 3 600 units for a whole message and the format's
limit of 2 000 bytes for the hidden one (2026-11-08). The app's cap is
reached first: about 1 700 bytes fit (threat model, §1). The stream limit of
4 000 bytes follows from the boundary.

**May change before 1.0:** the marker `STYP`, the 64-byte padding step and
the domain string `stypo-v1-header`.

## Stability

Not frozen yet. Once the formats are frozen, a change that breaks a decoder
gets a new version number and a new file.

Only the decode path is normative. Where an encoder places the run and how
much it allows are recommendations (`text-layer.md` §3, §4).

## A note on transport

How a message reaches the recipient is outside the wire format: the
reference decoder takes the text from any source. The app adds the finished
text to Messages' own field (`MSConversation.insertText`), and the recipient
drags or pastes the bubble. What was measured about delivery is in
`text-layer.md` §6 and in the threat model, §3.4.

## Threat model and reports

This directory defines a wire format, not a threat model. What the formats
protect, what they do not and how we know is in
[`THREAT_MODEL.md`](THREAT_MODEL.md).

Found a difference between the app and this spec? Open an issue at
<https://github.com/axlerk/stypo-protocol/issues>. For an attack on the
format, write first to hello@onegoodman.studio with `[SECURITY]` in the
subject.

## License

| What | License | Text |
|------|---------|------|
| Reference decoder and emitter (`reference/`) | Apache-2.0 | [`LICENSE`](LICENSE) |
| Specification text (`*.md` in this directory) | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
| Test vectors (`test-vectors/`) | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
| [`THREAT_MODEL.md`](THREAT_MODEL.md), published with the spec | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
| `legal/` (privacy policy, support page) | not covered: all rights reserved | — |

Copyright 2026 Pavel Khudiakov
([OneGoodMan.studio](https://onegoodman.studio)); see [`NOTICE`](NOTICE).
Writing your own implementation of the format is what this repository is
for: no permission needed, attribution appreciated.
