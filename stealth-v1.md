# Stealth Mode v1 (stealth-v1)

The mode that protects the content. Without the password, the stream is
computationally indistinguishable from uniformly random bytes: no magic, no length
field, no fixed structure. It does **not** hide that a run of variation selectors
exists, nor roughly how long it is ([`text-layer.md`](text-layer.md)).

For what this protects and what it does not, see the threat model
([`THREAT_MODEL.md`](THREAT_MODEL.md)). This document defines the wire format.

> **Status.** The shape follows Stiger's `stealth-v3` and Stecho's `stealth-v2`
> (same crypto, no permutation layer). The 64-byte bucket and the `stypo-v1-header`
> domain string are proposals; the owner has not signed them off. The body limit
> (2 000 bytes) is approved by the owner on 2026-11-08 (relayed by the design session).

> **Notation.** All multi-byte integers are big-endian. `||` is concatenation.
> `[a..b]` is a half-open byte slice.

## 1. Inputs

- `password`: the UTF-8 bytes of the user's passphrase. Non-empty.
- `stream`: the bytes from the text layer ([`text-layer.md`](text-layer.md), section 2).

There is no permutation: the stream is read in order, so there is nothing keyed by the
password before the header.

## 2. Stream layout

```
offset      size              field
------      ----------------  ----------------------------------------------
  0          16               salt
 16           4               marker
 20           1               maskedVersion
 21           1               maskedReserved
 22          12               nonce
 34          64 * k           ciphertext   (k >= 1)
 34 + 64k    16               tag
```

The stream is `50 + 64k` bytes. There is **no plaintext length field**; the real
length of the secret is inside the encrypted block.

## 3. Key derivation

```
mainKey = PBKDF2-HMAC-SHA256(
              password = password,
              salt     = salt,                  # the 16 bytes at offset 0
              iter     = 600000,
              dkLen    = 32)

derived = HKDF-SHA256(
              ikm  = mainKey,
              salt = empty,                     # zero-length, RFC 5869
              info = b"stypo-v1-header",        # ASCII, 15 bytes
              L    = 34)

macKey = derived[0 .. 32]
mask   = derived[32 .. 34]
```

(HKDF with an empty salt: the extract step is `PRK = HMAC-SHA256(32 zero bytes, ikm)`,
which is what CryptoKit's `HKDF<SHA256>` does without a salt.) The `info` string is
Stypo's own, so no key or marker is shared with Stiger or Stecho.

## 4. Marker and version

```
expected = HMAC-SHA256(macKey, salt || maskedVersion || maskedReserved)[0 .. 4]
require constant_time_equal(expected, marker)
```

A mismatch is `no-payload`: the password is wrong, or the message is not a Stypo
stealth message, or the header was changed. **A wrong password and a message that is
not Stypo give the same result**, with no other information.

When the marker matches, the password is right (a wrong one passes with probability
2^-32) and every later failure is about this message:

```
version  = maskedVersion  XOR mask[0]    require 0x01   else `unsupported`
reserved = maskedReserved XOR mask[1]    require 0x00   else `unsupported`
```

## 5. Decryption

```
let n = (stream length) - 22 - 12 - 16          # the ciphertext length
require n >= 64 and n mod 64 == 0               # else `truncated`
plaintextBlock = AES-256-GCM-Open(key = mainKey, nonce = stream[22..34],
                                  ciphertext = stream[34 .. 34+n],
                                  tag = stream[34+n ..], aad = empty)
                                                # authentication failure: `invalid`
```

Truncation shows as a length that is not `50 + 64k`: a run cut anywhere except at a
bucket boundary, after the header has been checked, is `truncated`. A cut that lands
exactly on a bucket boundary fails authentication and is `invalid`; a product
may say "cut or damaged" for both. The associated data is empty; the header is
authenticated by the marker.

`plaintextBlock` is `64k` bytes:

```
offset  size            field
------  --------------  -----------------------------------------------------
  0      2              length   = uint16, big-endian
  2      length         message  = the secret
  2+L    64k - 2 - L    padding  = uniformly random bytes
```

The decoder MUST reject (`invalid`): `length == 0`, `length > 64k - 2`,
`length > 2000` (the body limit, owner-approved). The padding carries no meaning.

## 6. Why each field is shaped this way

- **Salt first, marker, masked version and reserved**: as in `stealth-v3`; the masked
  bytes are authenticated by the marker, so a future flag in the reserved byte is
  tamper-evident, and neither carries a fixed value on the wire.
- **No length field**: the length is inside the encrypted block, so the stream has no
  low-entropy field.
- **Padding to a 64-byte bucket**: the stream's length reveals the secret's size
  only to the bucket (`k`); Stiger pads to the carrier's capacity, and a message has no
  capacity to fill. The bucket is a trade: a smaller one leaks more, a larger one costs
  more units of the message.
- **No permutation**: the stream is sequential; permuting a run of selectors would
  hide nothing a decoder with the password cannot undo, and the order is visible
  anyway.

## 7. Cost in the message

The smallest stealth message has `k = 1`: a stream of 114 bytes, at most 228 UTF-16
units (mean about 221). A secret of up to 62 bytes fits in one bucket (2 bytes go to
the length). Each further bucket adds 64 bytes, at most 128 units.

At the cap of 3 600 units with a 100-unit cover the stream may hold at
most 1 750 bytes in the worst case (2 units a byte), so `50 + 64k <= 1 750`, `k <= 26`:
a block of 1 664 bytes and a secret of up to 1 662 bytes, guaranteed. With
uniformly random bytes the mean cost is 1.9375 units, so `k = 27` (a 1 778-byte stream)
usually fits as well; the encoder counts the exact units and refuses what does not.
The arithmetic is in [`text-layer.md`](text-layer.md), section 4 (the cap is owner-approved).

## 8. Reference

Python reference decoder, written from these documents only:
[`reference/python/stypo_decode.py`](reference/python/stypo_decode.py). Test vectors
from the Python emitter [`reference/python/stypo_vectors.py`](reference/python/stypo_vectors.py)
are in [`test-vectors/`](test-vectors/); the Swift engine will decode them and
emit vectors that the Python decoder reads (plan step 4).
