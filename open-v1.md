# Open Mode (open-v1)

**Open mode is not a privacy feature.** Anyone who reads this document and
writes 30 lines of Python can read every open-mode message. It exists so the app
is useful before the user pays for stealth mode, and for messages you would
also write on a postcard.

Its magic is a fingerprint on purpose: a person who finds the run and reads the
stream sees `STYP` and learns which app made it. A message that must not say
that is a stealth message, and stealth mode does not hide that a run exists
either ([`text-layer.md`](text-layer.md)).

> **Status.** The magic `STYP` and the 2-byte length are proposals of the design
> session; the owner has not signed them off. The body limit (2 000 bytes) is a format
> ceiling under the verified collapse boundary, approved by the owner on 2026-11-08 (relayed by the design session) (see
> [`text-layer.md`](text-layer.md), section 4).

## 1. Framing

The stream (see [`text-layer.md`](text-layer.md), section 2) is exactly one frame:

```
offset  size  field
------  ----  -----------------------------------------------------------
  0      4    magic            = 0x53 0x54 0x59 0x50   ("STYP", ASCII)
  4      1    version          = 0x01
  5      2    payloadLength    = uint16, big-endian
  7      L    payload          = raw bytes, length = payloadLength
```

The stream is exactly `7 + L` bytes long: the encoder writes nothing after the
frame, and a run with bytes after it is not a frame.

A decoder returns, in this order of checks (results are defined in
[`text-layer.md`](text-layer.md), section 5):

| condition | result |
|---|---|
| stream shorter than 7 bytes, or magic not `STYP` | `no-payload` |
| `version` is not `0x01` | `unsupported` |
| `payloadLength` is `0`, or greater than **2 000** (owner-approved ceiling) | `invalid` |
| stream shorter than `7 + payloadLength` | `truncated` |
| stream longer than `7 + payloadLength` | `invalid` |
| otherwise | `ok`, the payload |

An empty secret is not a message: no encoder writes `payloadLength = 0`, and a
decoder rejects it (test vector `open-zero-length`).

The 2 000-byte limit follows from the collapse boundary: at least one UTF-16
unit per byte and 4 000 units in a message that is shown whole means no message
that arrives whole holds more than 4 000 stream bytes, and the cap leaves room
for far fewer; 2 000 is the format's own ceiling, fixed here so that two
implementations agree (owner-approved).

## 2. Payload semantics

At the wire-format level the payload is opaque bytes. The app layer uses UTF-8
text; that is not part of this spec.

## 3. Cost in the message

`STYP` is four bytes of 0x53 to 0x50, each 2 units; the version byte 0x01 is 1 unit
(a BMP selector); the length bytes are 1 or 2 units each; text bytes at or above
0x20 are 2 units each. A 100-byte ASCII secret costs about 4 + 1 + 3 + 200 = 208
units.

## 4. What "open" means

Anyone who can copy the message can read the payload. There is no integrity
check, no encryption, no obfuscation.
