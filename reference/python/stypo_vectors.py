# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pavel Khudiakov
"""Emits the Stypo test vectors: `spec/test-vectors/*.txt` and `manifest.json`.

    python stypo_vectors.py <out-dir>

A small encoder, written from `spec/text-layer.md`, `open-v1.md` and `stealth-v1.md`.
The encoder is **not** part of the wire format (only decoding is normative); it exists
to make messages, including malformed ones, for the decoders to read. The Swift engine
(plan step 4) decodes these files (CrossImplVectorsTests) and emitted `swift-v1/` for
stypo_decode.py to read, which is the independent check: this file and stypo_decode.py share
their key derivation, so a mistake there would not be caught by the pair alone.

Vectors are deterministic: salts, nonces, padding and filler text come from SHA-256 in
counter mode, so the same script gives the same bytes. A shipping encoder MUST use a
fresh random salt and nonce for every message; fixed ones are for vectors only.

The two size numbers are passed to the vectors as named constants: CAP_UNITS (owner-approved
2026-11-08) and BOUNDARY_UNITS (verified, 2026-11-08).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import stypo_decode as dec

# spec/text-layer.md, section 4: the cap is owner-approved (2026-11-08), the boundary is
# verified on iOS 26.7.2, 27.0 (simulator) and 27.2 (docs/experiment-read-path.md).
CAP_UNITS = 3600
BOUNDARY_UNITS = 4000
COLLAPSED_SHOWN_UNITS = 499     # a collapsed bubble shows (and a drag delivers) this many units

PASSWORD = "correct horse battery staple"
OTHER_PASSWORD = "Tr0ub4dor&3"


def prng(label: str, n: int) -> bytes:
    out, counter = b"", 0
    while len(out) < n:
        out += hashlib.sha256(f"stypo-vectors:{label}:{counter}".encode()).digest()
        counter += 1
    return out[:n]


def filler(label: str, nbytes: int) -> str:
    """ASCII text of exactly nbytes characters: words of 3 to 8 letters, single spaces."""
    raw = prng(label, nbytes * 2 + 16)
    out, total, i = [], 0, 0
    while total < nbytes:
        word = "".join(chr(97 + raw[(i * 8 + k) % len(raw)] % 26) for k in range(3 + raw[i % len(raw)] % 6))
        out.append(word)
        total += len(word) + 1
        i += 1
    return " ".join(out)[:nbytes]


def units(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


@lru_cache(maxsize=None)
def keys(password: str, salt: bytes):
    return dec.derive_header_keys(password, salt)


# --- encoders ---------------------------------------------------------------


def encode_open(body: bytes, version: int = 1, length: int | None = None, trailing: bytes = b"") -> bytes:
    n = len(body) if length is None else length
    return dec.OPEN_MAGIC + bytes([version]) + n.to_bytes(2, "big") + body + trailing


def encode_stealth(secret: bytes, password: str, label: str, version: int = 1, reserved: int = 0,
                   inner_length: int | None = None) -> bytes:
    salt = prng(f"salt:{label}", 16)
    nonce = prng(f"nonce:{label}", 12)
    k = max(1, -(-(2 + len(secret)) // dec.BUCKET))
    n = len(secret) if inner_length is None else inner_length
    block = n.to_bytes(2, "big") + secret + prng(f"pad:{label}:{len(secret)}", dec.BUCKET * k - 2 - len(secret))
    main_key, mac_key, mask = keys(password, salt)
    masked_version, masked_reserved = version ^ mask[0], reserved ^ mask[1]
    marker = hmac.new(mac_key, salt + bytes([masked_version, masked_reserved]), hashlib.sha256).digest()[:4]
    sealed = AESGCM(main_key).encrypt(nonce, block, None)          # ciphertext || tag
    return salt + marker + bytes([masked_version, masked_reserved]) + nonce + sealed


def run_text(stream: bytes) -> str:
    return "".join(chr(dec.byte_to_vs(b)) for b in stream)


def compose(cover: str, stream: bytes, at: int) -> str:
    """The run goes after the first `at` scalars of the cover."""
    return cover[:at] + run_text(stream) + cover[at:]


def cut_units(text: str, limit: int) -> str:
    """The first `limit` UTF-16 units of the text, cut at a scalar boundary."""
    out, used = [], 0
    for ch in text:
        u = 2 if ord(ch) > 0xFFFF else 1
        if used + u > limit:
            break
        out.append(ch)
        used += u
    return "".join(out)


def largest(build, limit: int):
    """The largest secret length n whose message has at most `limit` units."""
    lo, hi = 1, limit
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if units(build(mid)) <= limit:
            lo = mid
        else:
            hi = mid - 1
    return lo


# --- the vectors ------------------------------------------------------------

COVER = "See you at the station at eight."
COVER_AT = 3                                  # after "See"
COVER_RU = "Встретимся на вокзале в восемь."
COVER_RU_AT = 10                              # after "Встретимся"
COVER_EMOJI = "❤️ hello, see you at eight."   # heart + U+FE0F, then a space
COVER_IVS = "辻\U000e0100 and 葉\U000e0101 meet at eight."
COVER_KEYCAP = "1️⃣ first, then eight."


def vectors():
    v = []

    def add(name, mode, text=None, raw=None, cover=None, at=None, secret=None, password=None,
            decoder_password=None, expect="ok", encrypted=None, note=""):
        v.append(dict(name=name, mode=mode, text=text, raw=raw, cover=cover, at=at, secret=secret,
                      password=password, decoder_password=decoder_password, expect=expect,
                      encrypted=encrypted, note=note))

    def open_msg(name, cover, at, secret, note="", **kw):
        body = secret.encode()
        add(name, "open", compose(cover, encode_open(body), at), cover=cover, at=at, secret=secret,
            expect="ok", encrypted=False, note=note, **kw)

    def stealth_msg(name, cover, at, secret, note="", password=PASSWORD, **kw):
        stream = encode_stealth(secret.encode(), password, name)
        add(name, "stealth", compose(cover, stream, at), cover=cover, at=at, secret=secret, password=password,
            decoder_password=password, expect="ok", encrypted=True, note=note, **kw)

    # -- good messages
    open_msg("open-hello", COVER, COVER_AT, "hello world", "Smallest open message.")
    open_msg("open-cyrillic", COVER_RU, COVER_RU_AT, "Привет, это тест.", "Multi-byte secret and a Cyrillic cover.")
    stealth_msg("stealth-hello", COVER, COVER_AT, "hello world", "Smallest stealth message: one 64-byte bucket.")
    stealth_msg("stealth-cyrillic", COVER_RU, COVER_RU_AT,
                "Встретимся на вокзале в восемь, возьми зелёную папку и не опаздывай, пожалуйста: поезд ждать не будет.",
                "A secret of 184 UTF-8 bytes: three buckets.")
    stealth_msg("stealth-two-buckets", COVER, COVER_AT, filler("two-buckets", 100), "100 bytes of secret: 2 buckets.")
    stealth_msg("stealth-exactly-one-bucket", COVER, COVER_AT, filler("one-bucket", 62),
                "62 bytes of secret fill the first bucket exactly (2 + 62 = 64).")
    stealth_msg("stealth-just-over-one-bucket", COVER, COVER_AT, filler("over-bucket", 63),
                "63 bytes need a second bucket.")
    # Covers that carry variation selectors of their own.
    open_msg("open-emoji-cover-fe0f", COVER_EMOJI, 3, "hello world",
             "The cover starts with an emoji carrying U+FE0F; the run goes after the space that follows it, "
             "never adjacent to the emoji's own selector.")
    stealth_msg("stealth-emoji-cover-fe0f", COVER_EMOJI, 3, "hello world", "As above, stealth.")
    open_msg("open-ivs-cover", COVER_IVS, 3, "hello world",
             "Two CJK ideographic variation sequences in the cover (runs of one); the payload run is the longest.")
    open_msg("open-keycap-cover", COVER_KEYCAP, 4, "hello world", "A keycap in the cover (a run of one).")
    run3 = "x️️️ y and then some text to carry it."
    open_msg("open-cover-run-of-three", run3, 6, "hello world",
             "A cover with its own run of three selectors; the payload run is longer and wins.")
    # Size.
    def stealth_build(n):
        return compose(COVER, encode_stealth(filler("max", n).encode(), PASSWORD, "stealth-max-cap"), COVER_AT)
    n = largest(stealth_build, CAP_UNITS)
    stealth_msg("stealth-max-cap", COVER, COVER_AT, filler("max", n),
                f"The largest stealth message within CAP_UNITS = {CAP_UNITS} (owner-approved): a {n}-byte secret.")
    n = largest(lambda m: compose(COVER, encode_stealth(filler("bnd", m).encode(), PASSWORD, "stealth-at-boundary"), COVER_AT),
                BOUNDARY_UNITS)
    stealth_msg("stealth-at-boundary", COVER, COVER_AT, filler("bnd", n),
                f"The largest stealth message within BOUNDARY_UNITS = {BOUNDARY_UNITS} (verified): over the cap, "
                "still whole in a bubble on iOS 26.7.2, 27.0 (simulator) and 27.2.")
    n = largest(lambda m: compose(COVER, encode_open(filler("omax", m).encode()), COVER_AT), CAP_UNITS)
    open_msg("open-max-cap", COVER, COVER_AT, filler("omax", n),
             f"The largest open message within CAP_UNITS = {CAP_UNITS} (owner-approved): a {n}-byte secret.")

    # -- a collapsed bubble: the run is cut
    full = compose(COVER, encode_open(filler("cut", 600).encode()), COVER_AT)
    add("open-cut-499", "open", cut_units(full, COLLAPSED_SHOWN_UNITS), cover=COVER, at=COVER_AT, expect="truncated",
        note="An open message of 600 bytes cut to the 499 units a collapsed bubble shows (and a drag delivers).")
    stream = encode_stealth(filler("cut2", 600).encode(), PASSWORD, "stealth-cut-499")
    add("stealth-cut-499", "stealth", cut_units(compose(COVER, stream, COVER_AT), COLLAPSED_SHOWN_UNITS), cover=COVER,
        at=COVER_AT, password=PASSWORD, decoder_password=PASSWORD, expect="truncated",
        note="A stealth message of 600 bytes cut to 499 units: the marker passes, the frame is short.")
    stream = encode_stealth(b"hello world", PASSWORD, "stealth-cut-tail-5")
    add("stealth-cut-tail-5", "stealth", compose(COVER, stream[:-5], COVER_AT), cover=COVER, at=COVER_AT,
        password=PASSWORD, decoder_password=PASSWORD, expect="truncated",
        note="Five stream bytes missing at the end: not 50 + 64k.")
    stream = encode_stealth(b"hello world", PASSWORD, "stealth-cut-in-header")
    add("stealth-cut-in-header", "stealth", compose(COVER, stream[:20], COVER_AT), cover=COVER, at=COVER_AT,
        password=PASSWORD, decoder_password=PASSWORD, expect="no-payload",
        note="Cut inside the 22-byte header: nothing to check, so no payload (a cut here is not reported as truncated).")
    add("open-cut-in-header", "open", compose(COVER, encode_open(b"hello world")[:6], COVER_AT), cover=COVER, at=COVER_AT,
        expect="no-payload", note="Six stream bytes: shorter than the smallest frame (7).")
    stream = encode_open(b"hello world")
    add("open-cut-body", "open", compose(COVER, stream[:-4], COVER_AT), cover=COVER, at=COVER_AT, expect="truncated",
        note="The header is whole, four body bytes are missing.")

    # -- wrong password, not Stypo: the same answer
    stream = encode_stealth(b"hello world", PASSWORD, "stealth-hello")
    add("stealth-wrong-password", "stealth", compose(COVER, stream, COVER_AT), cover=COVER, at=COVER_AT,
        password=PASSWORD, decoder_password=OTHER_PASSWORD, expect="no-payload",
        note="The stealth-hello message with another password: the same result as a message that is not Stypo.")
    add("plain-text-no-payload", "none", COVER, cover=COVER, decoder_password=OTHER_PASSWORD, expect="no-payload",
        note="Ordinary text with no run, tried with a password: identical result to stealth-wrong-password.")
    add("stealth-no-password", "stealth", compose(COVER, stream, COVER_AT), cover=COVER, at=COVER_AT, password=PASSWORD,
        decoder_password=None, expect="no-payload",
        note="A stealth message tried without a password: open mode finds no magic.")

    # -- crafted frames
    def crafted(name, stream_bytes, expect, note, decoder_password=None, mode="open", password=None, at=COVER_AT):
        add(name, mode, compose(COVER, stream_bytes, at), cover=COVER, at=at, expect=expect, note=note,
            password=password, decoder_password=decoder_password)

    crafted("open-zero-length", encode_open(b""), "invalid", "payloadLength 0: an empty secret is not a message.")
    crafted("open-bad-version", encode_open(b"hello world", version=2), "unsupported", "version 0x02.")
    crafted("open-bad-magic", b"STEG" + encode_open(b"hello world")[4:], "no-payload", "Stiger's magic, not Stypo's.")
    crafted("open-length-too-big", encode_open(b"a" * 2001), "invalid", "payloadLength 2001 (limit 2000, a ceiling, owner-approved).")
    crafted("open-trailing-bytes", encode_open(b"hello", trailing=b"\x01\x02\x03"), "invalid", "Three bytes after the frame.")
    crafted("stealth-unsupported-version", encode_stealth(b"hello world", PASSWORD, "sv", version=2), "unsupported",
            "Version 0x02 under a valid marker.", decoder_password=PASSWORD, mode="stealth", password=PASSWORD)
    crafted("stealth-nonzero-reserved", encode_stealth(b"hello world", PASSWORD, "sr", reserved=1), "unsupported",
            "Reserved byte 0x01 under a valid marker.", decoder_password=PASSWORD, mode="stealth", password=PASSWORD)
    good = bytearray(encode_stealth(b"hello world", PASSWORD, "tamper"))
    good[40] ^= 0x01
    crafted("stealth-tampered-ciphertext", bytes(good), "invalid", "One flipped ciphertext bit: authentication fails.",
            decoder_password=PASSWORD, mode="stealth", password=PASSWORD)
    crafted("stealth-inner-length-zero", encode_stealth(b"hello world", PASSWORD, "ilz", inner_length=0), "invalid",
            "A valid seal around a block whose length field is 0.", decoder_password=PASSWORD, mode="stealth", password=PASSWORD)
    crafted("stealth-inner-length-too-big", encode_stealth(b"hello world", PASSWORD, "ilb", inner_length=500), "invalid",
            "A valid seal around a block whose length field exceeds the block.", decoder_password=PASSWORD,
            mode="stealth", password=PASSWORD)

    # -- negative: an encoder-rule violation
    add("negative-adjacent-fe0f", "negative", compose(COVER_EMOJI, encode_open(b"hello world"), 2), cover=COVER_EMOJI, at=2,
        expect="no-payload",
        note="The run placed right after the emoji's own U+FE0F (an encoder-rule violation): the stream starts with a "
             "stray 0x0F and no frame is read. This is why the encoder never places the run next to a selector.")

    # -- bytes that are not text
    add("invalid-utf-8", "none", raw=b"See you \xff\xfe at eight.", expect="no-payload",
        note="Not valid UTF-8: not a message.")
    return v


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generator": "spec/reference/python/stypo_vectors.py",
        "spec_version": "stealth-v1 / open-v1 / text-layer",
        "size_numbers": {"CAP_UNITS": CAP_UNITS, "BOUNDARY_UNITS": BOUNDARY_UNITS, "note":
                         "cap: owner-approved 2026-11-08; boundary: verified 2026-11-08 on iOS 26.7.2, 27.0 simulator, 27.2"},
        "passwords": {"main": PASSWORD, "other": OTHER_PASSWORD},
        "vectors": [],
    }
    for item in vectors():
        data = item["raw"] if item["raw"] is not None else item["text"].encode("utf-8")
        name = item["name"]
        (out / f"{name}.txt").write_bytes(data)
        text = data.decode("utf-8", errors="replace")
        stream = dec.extract_run(text) if item["raw"] is None else None
        entry = {
            "name": name, "mode": item["mode"], "file": f"{name}.txt", "notes": item["note"],
            "decoder_password": item["decoder_password"], "expect": item["expect"],
            "utf8_bytes": len(data), "utf16_units": units(text) if item["raw"] is None else None,
            "stream_bytes": len(stream) if stream else 0, "sha256": hashlib.sha256(data).hexdigest(),
        }
        if item["cover"] is not None:
            entry["cover"] = item["cover"]
        if item["at"] is not None:
            entry["insert_at_scalar"] = item["at"]
        if item["expect"] == "ok":
            entry["expect_plaintext_utf8"] = item["secret"]
            entry["expect_encrypted"] = item["encrypted"]
        manifest["vectors"].append(entry)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(manifest['vectors'])} vectors in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
