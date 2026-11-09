# Stypo Wire-Format Specification

<!-- public-mirror-banner -->

> **Public mirror.** This repository is automatically synchronised from
> the `spec/` directory of the (private) Stypo source tree. Filing
> issues against the spec here is fine; canonical edits happen upstream
> and propagate on every push to Stypo's `main`.

**Status: drafted 2026-11-08 (plan step 2). Not published; no copy, site text or
claim refers to it yet.** This directory is the normative specification of the
formats Stypo hides inside an ordinary text message. It exists so that anyone can:

1. Read the spec and see what is on the wire.
2. Run the reference decoder (`reference/python/`) on a message.
3. Compare the result against vectors (`test-vectors/`).

If the app does anything different from what is written here, that is a bug.

**Stypo is the most detectable member of its family.** The hidden stream is a run
of variation selectors that a one-line scan finds. Stealth mode protects the content,
not the existence of a message ([`text-layer.md`](text-layer.md); the threat model is
[`THREAT_MODEL.md`](THREAT_MODEL.md)).

## Layout

| File | What it covers |
|------|----------------|
| [`text-layer.md`](text-layer.md) | Bytes as variation selectors; the extraction rule; placement; the size boundary and cap; decoder results. Shared by both modes. |
| [`open-v1.md`](open-v1.md) | Open mode framing: public, no privacy, a fingerprint by design. |
| [`stealth-v1.md`](stealth-v1.md) | Stealth mode framing and cryptography. |
| [`reference/python/`](reference/python/) | Reference decoder, the vector emitter and the checker. |
| [`test-vectors/`](test-vectors/) | Messages, passwords and expected results. |

## What is measured and what is a proposal

The collapse boundary of 4 000 UTF-16 units is **verified** on iOS 26.7.2, 27.0 (simulator)
and 27.2 (`../docs/experiment-read-path.md`). The cap of 3 600 units and the body limit of
2 000 bytes are decisions the owner approved on 2026-11-08 (the 4 000-byte stream limit follows
from the boundary). The magic `STYP`, the 64-byte bucket and the domain string
`stypo-v1-header` are proposals the owner has not signed off. Nothing here is frozen until
the spec is published.

## Stability

Not frozen. Once published, `open-v1` and `stealth-v1` are frozen the way
Stiger's formats are: an incompatible change needs a new version number and a new
file. Only the decode path is normative; the encoder's choices (placement,
cap) are recommendations in `text-layer.md`.

## A note on transport

How a message reaches the recipient (the composer's `MSConversation.insertText`,
the bubble, a drag or a paste) is outside the wire format. What was measured about
it is in `text-layer.md`, section 6, and `../docs/experiment-read-path.md`.

## License

| What | License | Text |
|------|---------|------|
| Reference decoder and emitter (`reference/`) | Apache-2.0 | [`LICENSE`](LICENSE) |
| Specification text (`*.md` here) | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
| Test vectors (`test-vectors/`) | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
| Threat model ([`THREAT_MODEL.md`](THREAT_MODEL.md), published with the spec) | CC BY 4.0 | [`LICENSE-DOCS`](LICENSE-DOCS) |
