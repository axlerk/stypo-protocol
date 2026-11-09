# Reference decoder (Python)

| File | What |
|---|---|
| `stypo_decode.py` | The decoder, written from `../../*.md`. CLI: `python stypo_decode.py message.txt [--password P]` |
| `stypo_vectors.py` | A small encoder that emits `../../test-vectors/`. Not part of the wire format |
| `verify_test_vectors.py` | Checks every vector against the decoder |

**Dependencies: the Python standard library and one package, `cryptography` (PyCA),
for AES-256-GCM, which the standard library does not have.** PBKDF2, HMAC and HKDF are
the standard library's. This is what the plan allows ("only if unavoidable"): there is
no AES-GCM in `hashlib`, and a hand-written one would be worse in a reference.

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python verify_test_vectors.py ../../test-vectors
python stypo_vectors.py ../../test-vectors      # regenerate (deterministic)
```

`stypo_vectors.py` shares its key derivation with `stypo_decode.py`, so a mistake in that
derivation would not be caught by this pair. The independent check is the Swift engine
(`StypoCore/TextStegoEngine.swift`, plan step 4), checked in both directions on 2026-11-08: the
Swift decoder reads every vector in `../../test-vectors/` (36 of 36), and this decoder reads the 14
vectors the Swift encoder wrote to `../../test-vectors/swift-v1/` (14 of 14). The two implementations
use different libraries for PBKDF2, HKDF, HMAC and AES-GCM (CommonCrypto and CryptoKit against
`hashlib` and PyCA `cryptography`).

`verify_test_vectors.py` also checks the HKDF-SHA256 here against RFC 5869, test case 3 (a
zero-length salt and info), which is the empty-salt form stealth mode uses. PBKDF2, HMAC
and AES-GCM are the libraries' own.
