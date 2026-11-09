# Text Layer (text-layer)

How a byte stream travels inside an ordinary text message, and how a decoder
gets it back. Shared by both modes ([`open-v1.md`](open-v1.md),
[`stealth-v1.md`](stealth-v1.md)).

**Stypo is the most detectable member of its family.** The stream is a run of
variation selectors. A one-line scan for them finds the run in any message
that carries one, and ordinary text has at most one or two in a row. Nothing in
this layer hides that a message carries something; stealth mode hides what.

> **Status of the numbers in this file.** The collapse boundary (4 000 UTF-16
> units) is **verified** on iOS 26.7.2 and 27.2 (iPhone 12 mini and 15 Pro, real
> iMessage) and on the iOS 27.0 simulator, 2026-11-08. The cap (3 600 units) and the
> body limit (2 000 bytes) are **decisions**, approved by the owner on 2026-11-08
> (relayed by the design session), not measurements; the 4 000-byte stream limit is derived from the boundary. The
> record is `docs/experiment-read-path.md`. Statements are labelled **verified**
> (with the source), **inferred** or **unmeasured**.

> **Notation.** A message is a Unicode string; "scalar" is a Unicode scalar
> value; "unit" is a UTF-16 code unit. Messages travel as UTF-8.

## 1. Alphabet

One byte per variation selector. There are 256 of them:

```
byte 0x00..0x0F  ->  U+FE00 .. U+FE0F            (16, BMP:           3 bytes UTF-8, 1 UTF-16 unit)
byte 0x10..0xFF  ->  U+E0100 .. U+E01EF          (240, supplementary: 4 bytes UTF-8, 2 UTF-16 units)

scalar(b) = 0xFE00 + b            if b < 0x10
            0xE0100 + (b - 0x10)  otherwise
```

The mapping is Paul Butler's (2025), as used in the proof of concept. A decoder
reads a scalar back with the inverse; every other scalar is not part of the
alphabet.

Cost of a hidden byte in the message: **1 unit** if the byte is below `0x10`,
**2 units** otherwise. Worst case 2 per byte; for uniformly random bytes
(stealth mode) the mean is 1.9375.

Why this alphabet (**verified**, PoC `docs/experiment-text-carrier.md`, simulator
iOS 27.0 and phones iOS 26.7.2 / 27.2, 17 messages): variation selectors arrive
byte for byte through iMessage; they show no layout effect in a bubble up to
1 024 of them (zero-width joiners add 11 % to the bubble's height, tag
characters in runs of 64 or more are drawn as boxes, so those alphabets were
dropped).

## 2. Extraction: from a message to the stream

This is the normative part. The input is the message's text (the UTF-8 bytes of
the bubble, decoded; bytes that are not valid UTF-8 are not a Stypo message).

1. Split the message, in scalar order, into **maximal runs of consecutive
   alphabet scalars**.
2. The **payload run** is the longest run; if several have the same length, the
   first one. If there is no run, there is no payload.
3. The **stream** is the payload run mapped back to bytes (section 1).
4. If the stream is shorter than **7 bytes** (the smallest frame, open mode with a
   one-byte body) there is no payload. If it is longer than **4 000 bytes** there
   is no payload (derived from the verified boundary of section 4: no message at or
   under it has more than 4 000 alphabet scalars).

Nothing else in the message is read. The cover text is not parsed, normalised or
compared. A decoder MUST read the stream from the scalars of the UTF-8 bytes it
was given, and MUST NOT go through a normalising string API (**verified**, PoC:
a leading U+FEFF is dropped by Foundation's `String(data:encoding:)` as a byte-order
mark; the Swift decoder `String(decoding:as:)` keeps it).

The longest-run rule exists because a cover may carry variation selectors of its
own: an emoji such as U+2764 U+FE0F (one selector), a keycap (`1` U+FE0F U+20E3),
an ideographic variation sequence (a CJK character followed by one U+E0100..E01EF).
Those are runs of one or two scalars; the payload run is much longer (section 4).

## 3. Placement (encoder; not part of the decoder)

The encoder's choices do not change what a decoder does, so they are
recommendations with one hard rule, kept in this file so that every
implementation makes the same messages.

- **One run, in one place.** The run goes **at the end of the first word** (the grapheme
  clusters before the first space: "See" + run + " you at the station at eight.", as the
  PoC measured it) when that last cluster carries no variation selector and is not the last
  cluster of the cover; otherwise **after the first grapheme cluster that carries no
  variation selector and is not the last cluster** (an emoji or keycap first word makes the
  run go after the space that follows it). A variation selector joins the cluster before it, so the run makes the
  letter it follows one cluster with the hidden bytes (**verified**: a 92-selector
  run made 36 grapheme clusters of a 36-character cover).
- **Never adjacent to another variation selector of the cover.** An emoji cover
  `U+2764 U+FE0F` followed at once by the run would give one run of
  `FE0F + payload` and the stream would start with a stray `0x0F`: the decoder
  would read no frame. (This is a test vector, `negative-adjacent-fe0f`.) The
  rule above, "the first cluster without a selector", avoids it.
- **Never first or last in the message.** The cover needs at least two grapheme
  clusters, one of them before the run and one after.
- **The cover must not begin or end with U+000A, U+000D or U+FEFF.** **Verified**:
  a leading or trailing U+000A is dropped by Messages' composer at Send (the PoC's
  E03), and a leading U+FEFF is lost (the PoC's E11: no bubble at all on the
  phones). U+000D is **inferred** to behave like U+000A and **unmeasured**.
- **Every variation-selector run in the cover is at most 3 scalars**, so that the
  payload run (at least 7) is always the longest. The encoder checks the finished
  message by running the decoder's extraction on it and refusing if it does not
  return exactly the stream it put in.
- **The cover is the user's text, unchanged.** No normalisation, no trimming other
  than the rules above.

## 4. Size

### Collapse boundary

Messages draws a long text bubble collapsed (the first 499 units, an ellipsis and a
chevron). **Verified** (simulator iOS 27.0, 20 messages, `docs/experiment-read-path.md`):

- a bubble is **whole up to and including 4 000 UTF-16 units and collapsed from
  4 001** (a message of 4 000 units whole, one of 4 001 collapsed);
- the rule counts UTF-16 units, **not** UTF-8 bytes (8 436 bytes were whole at
  2 836 units and collapsed at 4 236) and not scalars;
- visible text collapses at the same length (4 049 units of ASCII: collapsed);
- the whole text of a collapsed bubble is **not** what a drag delivers: the drop
  carries only the 499 shown units, and the stream is cut there.

**Verified, 2026-11-08 (iOS 26.7.2, 27.0 simulator, 27.2):** **COLLAPSE_BOUNDARY =
4 000 units**. A message of 4 000 units was whole and one of 4 001 collapsed on
every device, as sent and as received; the same on the simulator. Other iOS
versions are **unmeasured**.

### The cap (encoder)

An encoder refuses a message whose length in UTF-16 units, cover and run together,
exceeds the cap.

*Decision, approved by the owner on 2026-11-08:* **CAP_UNITS = 3 600**, 10 %
under the verified boundary. The encoder knows the exact length, so the cap is exact: the
run costs `sum(1 if b < 0x10 else 2)` units. In the worst case (2 units a byte,
a cover of `c` units) the hidden stream is at most `(3 600 - c) / 2` bytes: 1 750
for a 100-unit cover. A cap in UTF-8 bytes would never be wrong (a message's bytes
are never fewer than its units) but would spend about half of what the boundary
allows; the encoder uses units.

A decoder does not enforce the cap. It enforces only the two constants of section 2
(a stream of 7 to 4 000 bytes) and the frame constants of each mode.

### Why a cut run is reported as cut

A collapsed bubble can reach the decoder as its first 499 units: the run is
cut and the frame is shorter than it says. A decoder reports this as
**truncated**, not as "not a Stypo message", whenever the frame proves it
(section 5), so that the person is told to ask for the message again or to
read it another way.

## 5. Decoder results

Every decoder, in every language, returns one of five results for a message:

| result | meaning |
|---|---|
| `ok` | a secret was recovered; the mode (open or stealth) is known |
| `no-payload` | no payload run, a run outside 7..4 000 bytes, no open magic, or a stealth marker that does not match. **A wrong password and a message that is not Stypo give this same result, on purpose** |
| `truncated` | the frame proves the run is shorter than the frame it announces (details in each mode) |
| `unsupported` | a version byte this decoder does not know (open: after the magic; stealth: after the marker has passed) |
| `invalid` | a frame of the right kind with impossible content (a zero length, an authentication failure, bytes after the frame) |

Order, given a stream: if a password is at hand, try stealth first; a stealth
marker that matches settles the result (the password is right, so `truncated`,
`unsupported` and `invalid` are about the message); a marker that does not match
falls through to open mode, as in the sibling formats. Without a password only
open mode is tried.

`truncated` and `invalid` after a passed stealth marker are reported only to a
person who holds the password; a person without it gets `no-payload` either way.

## 6. What the transport does (not normative)

Everything here is **verified** in the PoC unless marked: variation selectors,
zero-width and format characters, spaces, bidi controls, tag characters arrive
byte for byte in a bubble sent and received over iMessage (iOS 26.7.2 to 27.2) and
on the simulator; no Unicode normalisation is applied; the composer's
`MSConversation.insertText` holds the exact bytes (every insertion of the
simulator runs, 17 of 17 on the phones); a leading or trailing U+000A and a leading
U+FEFF are lost. SMS, other messengers and other iOS versions are **unmeasured**.
The threat model ([`THREAT_MODEL.md`](THREAT_MODEL.md)) says what none of this protects.
