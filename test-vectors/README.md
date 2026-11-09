# Test vectors

Messages (UTF-8 files), the password to try, and the expected result, emitted by
`../reference/python/stypo_vectors.py` and read by `stypo_decode.py`. The Swift engine decodes them
too (`StypoTests/CrossImplVectorsTests`), and `swift-v1/` holds 14 vectors the Swift encoder wrote
(`SwiftVectorEmitterTests`, with `EMIT_VECTORS=1`; random salts and nonces, committed once) for the Python decoder:
`python verify_test_vectors.py ../../test-vectors/swift-v1`.

- `manifest.json`: for each vector, the file, its SHA-256 and sizes, the cover and where the
  run was inserted, the password the *decoder* is given, and the expected result.
- `*.txt`: the messages. The hidden characters are invisible; open them with a hex dump.

Stealth vectors use fixed salts and nonces so the files are reproducible; a shipping
encoder uses fresh random ones. Size vectors depend on the two size numbers (the cap, owner-approved, and the verified
collapse boundary) and are regenerated if the cap changes.

What the vectors cover: open and stealth messages with an ASCII and a Cyrillic secret;
buckets of 1, 2 and 3; a cover with an emoji carrying U+FE0F, with ideographic variation
sequences, with a keycap, with a run of three selectors of its own; the largest messages
within the cap and the boundary; runs cut at 499 units (a collapsed bubble) and
elsewhere; a wrong password, a message that is not Stypo, and a stealth message without a
password (the first two must give the same result); crafted frames (zero length, bad
version, bad magic, too long, trailing bytes, unsupported stealth version, tampered
ciphertext, bad inner length); one encoder-rule violation (`negative-adjacent-fe0f`); and
bytes that are not UTF-8.

## Verify

```
cd ../reference/python
pip install -r requirements.txt
python verify_test_vectors.py ../../test-vectors
```
