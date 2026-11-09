# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pavel Khudiakov
"""Reference decoder for the Stypo wire format.

Written from `spec/text-layer.md`, `spec/open-v1.md` and `spec/stealth-v1.md`
only, with the Python standard library plus one primitive the standard library
does not have: AES-256-GCM, taken from PyCA `cryptography` (`AESGCM`). Everything
else (PBKDF2, HMAC, HKDF) is the standard library.

Usage:

    python stypo_decode.py message.txt
    python stypo_decode.py message.txt --password 'hunter2'
    python stypo_decode.py -                      # message on stdin, UTF-8

The input is the message as UTF-8 bytes (what a bubble holds). Exit status:

    0  decoded
    1  not decoded; the printed status says why (no payload, truncated,
       unsupported, invalid)
    2  bad arguments

Every number the spec leaves to a decision (owner-approved 2026-11-08) is a named constant below.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# Constants: spec/text-layer.md, spec/open-v1.md, spec/stealth-v1.md.
# ---------------------------------------------------------------------------

OPEN_MAGIC = b"STYP"           # proposal, owner has not signed off
OPEN_VERSION = 0x01
OPEN_HEADER_SIZE = 7           # magic 4 + version 1 + length 2

STEALTH_VERSION = 0x01
STEALTH_HEADER_SIZE = 22       # salt 16 + marker 4 + maskedVersion 1 + maskedReserved 1
SALT_LEN = 16
GCM_NONCE_LEN = 12
GCM_TAG_LEN = 16
LEN_PREFIX = 2
BUCKET = 64                    # proposal, owner has not signed off
HEADER_INFO = b"stypo-v1-header"
PBKDF2_ITER = 600_000

# spec/text-layer.md, section 4: the stream limit follows from the verified collapse boundary;
# the body limit is an owner-approved decision (a format ceiling, 2026-11-08).
MAX_STREAM_BYTES = 4000        # no message at or under the collapse boundary has more VS scalars
MAX_BODY_BYTES = 2000

MIN_STREAM_BYTES = 7           # shorter than any frame: no payload


class Status(Enum):
    OK = "ok"
    NO_PAYLOAD = "no-payload"      # also: wrong password, not Stypo (indistinguishable by design)
    TRUNCATED = "truncated"        # the run is structurally shorter than its own frame
    UNSUPPORTED = "unsupported"    # a version this decoder does not know
    INVALID = "invalid"            # right format, impossible content (length 0, tag fails, ...)


@dataclass
class Result:
    status: Status
    data: Optional[bytes] = None       # the secret, when status is OK
    encrypted: Optional[bool] = None   # True stealth, False open, None when not decoded
    detail: str = ""


# ---------------------------------------------------------------------------
# Text layer (spec/text-layer.md).
# ---------------------------------------------------------------------------


def vs_to_byte(cp: int) -> Optional[int]:
    """U+FE00..FE0F -> 0x00..0x0F, U+E0100..E01EF -> 0x10..0xFF, else None."""
    if 0xFE00 <= cp <= 0xFE0F:
        return cp - 0xFE00
    if 0xE0100 <= cp <= 0xE01EF:
        return cp - 0xE0100 + 16
    return None


def byte_to_vs(b: int) -> int:
    return 0xFE00 + b if b < 16 else 0xE0100 + b - 16


def extract_run(text: str) -> Optional[bytes]:
    """The longest maximal run of variation selectors, first one on a tie, as bytes."""
    best: list[int] = []
    current: list[int] = []
    for ch in text:
        b = vs_to_byte(ord(ch))
        if b is None:
            if len(current) > len(best):
                best = current
            current = []
        else:
            current.append(b)
    if len(current) > len(best):
        best = current
    return bytes(best) if best else None


# ---------------------------------------------------------------------------
# Open mode (spec/open-v1.md).
# ---------------------------------------------------------------------------


def decode_open(stream: bytes) -> Result:
    if len(stream) < OPEN_HEADER_SIZE or stream[:4] != OPEN_MAGIC:
        return Result(Status.NO_PAYLOAD, detail="no open-v1 magic")
    if stream[4] != OPEN_VERSION:
        return Result(Status.UNSUPPORTED, detail=f"open version {stream[4]:#04x}")
    length = int.from_bytes(stream[5:7], "big")
    if length == 0 or length > MAX_BODY_BYTES:
        return Result(Status.INVALID, detail=f"payloadLength {length}")
    if len(stream) < OPEN_HEADER_SIZE + length:
        return Result(Status.TRUNCATED, detail=f"{len(stream) - OPEN_HEADER_SIZE} of {length} body bytes")
    if len(stream) > OPEN_HEADER_SIZE + length:
        return Result(Status.INVALID, detail="bytes after the frame")
    return Result(Status.OK, data=stream[OPEN_HEADER_SIZE:], encrypted=False)


# ---------------------------------------------------------------------------
# Stealth mode (spec/stealth-v1.md).
# ---------------------------------------------------------------------------


def hkdf_sha256(ikm: bytes, info: bytes, length: int) -> bytes:
    """RFC 5869 HKDF-SHA256 with a zero-length salt (HMAC key of 32 zero bytes)."""
    prk = hmac.new(b"\x00" * 32, ikm, hashlib.sha256).digest()
    out, t, counter = b"", b"", 1
    while len(out) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        out += t
        counter += 1
    return out[:length]


def derive_header_keys(password: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    main_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITER, dklen=32)
    derived = hkdf_sha256(main_key, HEADER_INFO, 34)
    return main_key, derived[:32], derived[32:34]


def decode_stealth(stream: bytes, password: str) -> Result:
    if len(stream) < STEALTH_HEADER_SIZE:
        return Result(Status.NO_PAYLOAD, detail="shorter than the stealth header")
    salt = stream[0:16]
    marker = stream[16:20]
    masked_version, masked_reserved = stream[20], stream[21]
    main_key, mac_key, mask = derive_header_keys(password, salt)
    expected = hmac.new(mac_key, salt + bytes([masked_version, masked_reserved]), hashlib.sha256).digest()[:4]
    if not hmac.compare_digest(expected, marker):
        return Result(Status.NO_PAYLOAD, detail="marker mismatch")
    # From here on the password is right (a false pass has probability 2^-32): the failure
    # is about this message, not about who is asking.
    if masked_version ^ mask[0] != STEALTH_VERSION or masked_reserved ^ mask[1] != 0x00:
        return Result(Status.UNSUPPORTED, detail="stealth version or reserved byte")
    blob = stream[STEALTH_HEADER_SIZE:]
    # blob = nonce 12 + ciphertext 64*k + tag 16, k >= 1
    body = len(blob) - GCM_NONCE_LEN - GCM_TAG_LEN
    if body < BUCKET or body % BUCKET != 0:
        return Result(Status.TRUNCATED, detail=f"stream of {len(stream)} bytes is not 50 + 64k")
    try:
        block = AESGCM(main_key).decrypt(blob[:GCM_NONCE_LEN], blob[GCM_NONCE_LEN:], None)
    except Exception:
        return Result(Status.INVALID, detail="authentication failed")
    length = int.from_bytes(block[:LEN_PREFIX], "big")
    if length == 0 or length > len(block) - LEN_PREFIX or length > MAX_BODY_BYTES:
        return Result(Status.INVALID, detail=f"inner length {length}")
    return Result(Status.OK, data=block[LEN_PREFIX:LEN_PREFIX + length], encrypted=True)


# ---------------------------------------------------------------------------
# Top level.
# ---------------------------------------------------------------------------


def decode(text: str, password: Optional[str] = None) -> Result:
    stream = extract_run(text)
    if stream is None or len(stream) < MIN_STREAM_BYTES:
        return Result(Status.NO_PAYLOAD, detail="no variation-selector run")
    if len(stream) > MAX_STREAM_BYTES:
        return Result(Status.NO_PAYLOAD, detail="run longer than any message can carry")
    if password:
        result = decode_stealth(stream, password)
        if result.status is not Status.NO_PAYLOAD:
            return result            # the marker passed: this is a stealth message
        # Marker mismatch: wrong password or not stealth. Try open, as the siblings do.
    return decode_open(stream)


def decode_bytes(message: bytes, password: Optional[str] = None) -> Result:
    """The message as the bubble's UTF-8 bytes. Invalid UTF-8 is not a Stypo message."""
    try:
        text = message.decode("utf-8")
    except UnicodeDecodeError:
        return Result(Status.NO_PAYLOAD, detail="not UTF-8")
    return decode(text, password)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Reference decoder for Stypo messages.")
    parser.add_argument("path", help="File with the message (UTF-8), or - for stdin.")
    parser.add_argument("--password", default=None, help="Stealth-mode password.")
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read() if args.path == "-" else open(args.path, "rb").read()
    result = decode_bytes(raw, args.password)
    print(f"status: {result.status.value}" + (f" ({result.detail})" if result.detail else ""), file=sys.stderr)
    if result.status is not Status.OK:
        return 1
    print(f"mode: {'stealth' if result.encrypted else 'open'}", file=sys.stderr)
    try:
        print(result.data.decode("utf-8"))
    except UnicodeDecodeError:
        sys.stdout.buffer.write(result.data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
