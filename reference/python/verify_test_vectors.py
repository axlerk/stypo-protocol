# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pavel Khudiakov
"""Check every vector in a test-vectors folder against the reference decoder.

    python verify_test_vectors.py ../../test-vectors

For each vector: the file's SHA-256 and sizes match the manifest, and decoding it
(with the vector's `decoder_password`) gives the expected result and, for `ok`, the
expected secret and mode. Exit status 0 only if every vector passes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import stypo_decode as dec


def units(data: bytes) -> int | None:
    try:
        return len(data.decode("utf-8").encode("utf-16-le")) // 2
    except UnicodeDecodeError:
        return None


def self_test() -> bool:
    """HKDF against RFC 5869, test case 3 (zero-length salt and info): the one derivation the
    vectors and the decoder share, checked against a value that is not ours."""
    okm = dec.hkdf_sha256(bytes([0x0B]) * 22, b"", 42)
    return okm.hex() == ("8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d"
                         "9d201395faa4b61a96c8")


def run(folder: Path) -> int:
    print("HKDF-SHA256 against RFC 5869 test case 3:", "ok" if self_test() else "FAILED")
    if not self_test():
        return 1
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    failures = 0
    print(f"{'vector':36} {'expect':12} {'got':12} result")
    for v in manifest["vectors"]:
        data = (folder / v["file"]).read_bytes()
        problems = []
        if hashlib.sha256(data).hexdigest() != v["sha256"]:
            problems.append("sha256 differs from the manifest")
        if len(data) != v["utf8_bytes"]:
            problems.append("size differs from the manifest")
        if v["utf16_units"] is not None and units(data) != v["utf16_units"]:
            problems.append("UTF-16 length differs from the manifest")
        result = dec.decode_bytes(data, v["decoder_password"])
        if result.status.value != v["expect"]:
            problems.append(f"status {result.status.value}, expected {v['expect']}")
        elif v["expect"] == "ok":
            if result.data != v["expect_plaintext_utf8"].encode("utf-8"):
                problems.append("plaintext differs")
            if result.encrypted != v["expect_encrypted"]:
                problems.append("mode differs")
        print(f"{v['name']:36} {v['expect']:12} {result.status.value:12} {'ok' if not problems else '; '.join(problems)}")
        failures += bool(problems)
    print(f"{len(manifest['vectors']) - failures} of {len(manifest['vectors'])} vectors pass")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(run(Path(sys.argv[1])))
