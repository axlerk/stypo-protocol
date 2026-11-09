# Stypo — Threat Model

This document states what Stypo defends against, what it does **not** defend
against, and the assumptions behind those guarantees. Read it before trusting
the app with anything that matters.

**Stypo is the most detectable member of its family.** The hidden text rides
in a run of invisible variation-selector characters inside an ordinary text
message. A one-line scan for those characters finds the run. Nothing in the
design hides that a message carries something; the password hides what.

If you find a gap between this document and the implementation, the
implementation is wrong — please open an issue.

For the byte-for-byte wire format and an independent reference decoder you can
run yourself, see [`spec/`](spec/README.md).

Labels used throughout: **verified** (read in the code, or measured, with the
source named), **inferred** (reasoning from the design, not measured),
**unmeasured** (nobody has checked, and no claim is made). Measurements are in
`docs/experiment-read-path.md` and, for the proof of concept, in
`poc/docs/experiment-text-carrier.md`.

## TL;DR

**English.**

- **Protects, with a password:** the content of a short text (AES-256-GCM, key
  derived from the password by PBKDF2-SHA256, 600 000 iterations), and the fact
  that a search of the chat for words finds only the cover text the sender wrote
  (the hidden characters are not letters; inferred, the search itself was not
  tried).
- **Does not protect:** the **existence** of a hidden message. A run of
  variation selectors is an anomaly in any text, and a one-line scan finds it
  (ordinary text is expected to carry one or two of them next to an emoji, not a
  hundred: inferred, not measured). There is nothing here that resembles Stiger's or Stecho's attempt to match the
  statistics of a cover. A compromised or unlocked phone, a Keychain extracted
  by forensic tooling, and editing the message after it was added also defeat or
  destroy the protection.
- **Open mode** (no password) is readable by anyone with the spec and thirty
  lines of code, and its `STYP` magic names the app that wrote it. It is not a
  privacy feature, and it exposes the encrypted messages in the same chat by
  association.
- **Length leaks to a 64-byte bucket:** anyone who finds the run can count it.
- **No forward secrecy:** a leaked password decrypts every earlier message sent
  under it.
- **Copying into other apps, SMS and non-Apple recipients are unmeasured**
  (§1 lists what is) and are not claimed.

**По-русски.**

- **Защищает, с паролем:** содержимое короткого текста (AES-256-GCM, ключ
  выводится из пароля через PBKDF2-SHA256, 600 000 итераций) и то, что поиск по
  чату находит только видимый текст, который написал отправитель (скрытые
  символы не буквы; это вывод, сам поиск не пробовали).
- **Не защищает:** **сам факт** скрытого сообщения. Цепочка вариационных
  селекторов в любом тексте выглядит аномалией, и её находит проверка в одну
  строку (в обычном тексте ожидается один-два таких символа рядом с эмодзи, а
  не сотня: это вывод, не измерение). Здесь нет ничего похожего на попытку
  Stiger и Stecho повторить статистику видимого текста. Взломанный или разблокированный
  телефон, связка ключей Keychain, снятая криминалистическим инструментом, и
  правка сообщения после добавления тоже обходят защиту или уничтожают её.
- **Открытый режим** (без пароля) читает любой, у кого есть спецификация и
  тридцать строк кода, а его магическая метка `STYP` называет приложение,
  которое его написало. Это не приватность, и он по ассоциации выдаёт
  зашифрованные сообщения в том же чате.
- **Длина видна с точностью до корзины в 64 байта:** любой, кто нашёл цепочку,
  может её сосчитать.
- **Прямой секретности нет:** утёкший пароль расшифровывает все прежние
  сообщения, отправленные с ним.
- **Копирование в другие приложения, SMS и получатели не на устройствах Apple
  не измерены** (перечень в §1) и не заявляются.

## 1. Scope

Stypo hides a short text (at most 2 000 bytes, and at most 3 600 UTF-16 units
for the whole message, cover included) in an ordinary iMessage **text
message**. The sender writes a cover text; Stypo puts the secret into a run of
variation selectors (U+FE00..FE0F and U+E0100..E01EF, one byte per character)
at the end of the cover's first word, and adds the finished text to Messages'
own field through `MSConversation.insertText`. The recipient drags the bubble
into the Stypo extension, or copies it and pastes it there, and the extension
reads the run back.

Facts the design rests on, each with its source:

- **verified** The characters of the alphabet arrive byte for byte through
  iMessage: no normalisation, 4 049 bytes of selectors exact on the phones,
  16 145 bytes exact in the simulator (proof of concept, iPhone 12 mini on
  iOS 26.7.2 to iPhone 15 Pro on iOS 27.2, real iMessage, 17 messages, 12 read
  back exactly; iOS 27.0 simulator).
- **verified** A text bubble is drawn whole up to 4 000 UTF-16 units and
  collapsed from 4 001, on iOS 26.7.2, 27.0 (simulator) and 27.2. A collapsed
  bubble drags as its first 499 units, so the cap of the app is 3 600 units
  (`docs/experiment-read-path.md`).
- **verified** A drag of a whole incoming bubble delivered exact bytes 12 of 12
  on the two phones. The programmatic paste after Copy gave exact bytes 7 of 8
  behind the system prompt and was denied silently once on iOS 27.2; the iOS 27.0
  simulator returned nothing 6 of 6 and showed no prompt.
- **verified** One backspace in Messages' field after `insertText` removed the
  first word's last letter together with the whole hidden run (iOS 27.0
  simulator, press 30 of 36). Editing the text after it was added is not
  supported, and the composer says so.
- **verified** Pasting a copied bubble into Notes on the iPhone 12 mini (iOS 26.7.2) kept
  the 400-byte test message exactly (216 UTF-16 units, 92 selectors, SHA-256 equal). One
  message, one phone: the 15 Pro's three runs were inconclusive.
- **verified** A notification banner on an unlocked iPhone 15 Pro (iOS 27.2) and iPhone 12 mini
  (iOS 26.7.2), with Show Previews at When Unlocked or Always, showed the whole 400-byte test message as
  plain text (the 92 hidden characters add no gap, width or mark). For the 4 000-unit message the banner
  showed only the cover text up to the hidden run (`KD2 See`) and cut the rest without a mark. n = 1
  per cell (`docs/experiment-read-path.md`, "Phone round 2").
- **verified** Messages shows no "From <app>" label on a text bubble that an extension inserted with
  `insertText`: not on the sent bubble (iPhone 12 mini, iOS 26.7.2) and not on the received one (the 12 mini,
  and the iPhone 15 Pro on iOS 27.2), in the accessibility tree, the screenshot or the long-press menu.
  The same thread on the 12 mini shows "From Stecho" under a received video carrier of another app's
  extension, so the label exists for attachments. Stypo's text carries none.
- **verified** With VoiceOver on, focusing the composer that holds the 400-byte test message made the
  caption panel read "Message, Text field, Is editing, PV1 See you at the station a…" (the panel's width cuts
  the line). The panel shows the text that is spoken; an invisible character draws nothing in it, so
  whether the selectors were spoken is not shown. One phone (12 mini, iOS 26.7.2), n = 1.
- **Unmeasured, in one list** (nobody has checked, and no claim is made):
  - what travels with the message when it goes through the pasteboard (the recipient's Copy
    then paste; Stypo offers no "Copy instead of send"): what is stored, for how long, and what
    other apps and devices see;
  - the SMS fallback and any non-iMessage recipient;
  - copying into other messengers and apps (Notes on one phone is the only measurement);
  - the lock-screen preview (not measured: skipped by the owner's decision of 2026-11-08, on the design session's recommendation; see
    `docs/experiment-read-path.md`, "Phone round 2"), and the banner on other iOS versions;
  - what VoiceOver speaks for a received bubble (the runner's taps did not move the VoiceOver
    cursor onto a transcript cell; only the accessibility label, which holds every selector, is known),
    how long it takes, and the speech of the full composer line (the caption panel cuts it);
  - whether the banner's cut for long runs sets in below 3 964 selectors (two points: 92 shown whole,
    3 964 cut);
  - the Pro states and the biometric lock in the live UI (the screens were photographed
    in the simulator in the free state, no passcode);
  - a collapsed bubble copied on a phone; iOS versions other than 26.7.2, 27.0 (simulator)
    and 27.2; the Mac and Watch clients.

## 2. Adversaries we defend against

### A. Someone reading the chat, or searching it for words (with a password)
With a password the hidden bytes are the output of AES-256-GCM and a random
header: indistinguishable from random bytes without the key (`spec/stealth-v1.md`),
and mapped to invisible characters, not to letters. A person scrolling the chat
sees the cover text and nothing else; a keyword search of the chat can match
the cover and has no letters of the secret to match (**inferred**, the system
search was not tried). This is the whole of what the design offers against a
reader who is not looking for hidden characters. It is not protection against one
who is (§3, "Detection").

### B. Someone with a copy of the app or the spec
The format is public (`spec/`), and so are the app's own strings and the
reference decoder. A stealth message is not readable without the password:
the key comes from PBKDF2-HMAC-SHA256 with 600 000 iterations over a fresh
16-byte salt, and the ciphertext is authenticated (GCM tag, and a 4-byte
HMAC marker over the header). A wrong password and a message that is not Stypo give
the same answer, on purpose. The cost of guessing is the cost of PBKDF2 against
the password's own entropy: a weak password is a weak lock (the app shows a
strength colour; it does not enforce a floor).

## 3. Adversaries we do NOT defend against

The following are out of scope. If your threat model includes any of these,
Stypo is the wrong tool.

### Detection (the existence of a hidden message)
This is the main limit and the reason for the sentence at the top.

- A run of variation selectors is found by scanning the message for those code
  points; the decoder itself takes the longest run of them and treats a run of 7
  to 4 000 as a payload (`spec/text-layer.md` section 2). **Inferred:** ordinary
  text contains runs of one or two (an emoji with its presentation selector, a
  keycap, an ideographic variation sequence), so a long run stands out; nobody
  measured a corpus for this, and no figure is claimed.
- The smallest stealth message is a run of 114 characters; a typical one is
  hundreds. **verified** (arithmetic of the format, `spec/stealth-v1.md` section 7).
- The position is fixed: the run sits right after the first word of the cover
  (`spec/text-layer.md` section 3). A scanner that knows the app does not need to
  search.
- The cover is the sender's own text, unchanged (the only edits are the line
  breaks and U+FEFF a message cannot keep at its ends); the run is the only part
  of the message that is not ordinary text, and nothing makes it look like
  ordinary text.
- Stypo does nothing against a classifier, a log scan, a corpus search by an
  intermediary, or a person who copies the message into an editor that shows
  invisible characters. Stiger and Stecho at least try to match the statistics of
  a cover; Stypo has no such layer to approach, and none is planned.

### Length (to a 64-byte bucket)
A stealth message pads the secret to a multiple of 64 bytes inside the
encryption, so the run is `50 + 64k` bytes long (`spec/stealth-v1.md`). Anyone
who finds the run counts it and learns `k`, the secret's size to within one
bucket. Open mode has an exact length in clear. **Proposal, not signed off by the
owner:** the bucket size.

### Open mode is a public fingerprint
Open mode writes the magic `STYP`, a version and a length in clear
(`spec/open-v1.md`). A person who finds the run and reads it sees which app made
it, and reads the secret. It also tells an observer that the same tool is in use in
that chat, which exposes encrypted messages there by association. Fine for love
notes; never for anything sensitive. **Proposal, not signed off:** the magic.

### No forward secrecy
A password that leaks (shoulder-surfing, a phone with the Keychain extracted, a
backup of the person who knew it) decrypts every earlier message sent under it.
Passwords belong to chats, not to the person, so a leak is bounded by the chats
that share it.

### Compromised endpoint
- Malware on the sender's or recipient's phone, a keylogger, a screen recorder,
  anything reading the unlocked Keychain, a jailbroken phone.
- An **unlocked phone, or one with the app's biometric lock off** (the default):
  a saved password decrypts on drag-in, the app and the extension are visible on
  the phone, and the Messages thread holds the bubbles.
- Our password item uses `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`,
  which physically prevents iCloud Keychain sync of *our* item.

### Coercion
Someone who can force you to unlock the phone or give up the password. There is
no plausible-deniability mode and no duress password.

### Side channels
- Shoulder surfing while typing the secret or the password.
- Third-party keyboards with Full Access run in their own processes and can see
  every keystroke entered into the cover and secret fields. Password fields use
  secure text entry, which iOS answers with the system keyboard (Stiger's
  finding, inherited; not re-checked here); the two text fields do not.
- Drafts: an unfinished text is kept on the phone for up to 72 hours, sealed with
  a per-install key held in the Keychain (`ThisDeviceOnly`), cover and secret
  both. A person with the unlocked phone and the unlocked app reads it.
- Screenshots of the compose screen in the app switcher.
- **Reading by paste.** The recipient's own Copy in Messages puts the bubble on
  the system pasteboard, which Stypo does not control: the write is not
  `localOnly`, so the text may be relayed by Universal Clipboard to the
  recipient's other devices and stays on the pasteboard until replaced. **inferred**
  from Stiger's measurement for images; not measured for text. The drag path never
  touches the pasteboard.
- **Stypo offers no "Copy instead of send"** (owner's decision, 2026-11-08). In Stiger and Stecho it
  exists to drop the "From <app>" label that Messages puts under an extension's attachment; Messages puts
  none under text that an extension adds with `insertText` (§1, verified on two phones), so the reason
  does not apply, and the setting, its guide step and its paywall row are not shown. The code keeps a
  pasteboard branch (the exact UTF-8 bytes, `localOnly`) behind `ProductFeatures.manualSend`, which is off,
  so nothing reaches it, and a stored preference from an older build does nothing. If it were offered,
  anything else on the same phone that reads the pasteboard right after would be out of scope (recalled,
  not verified here: the pasteboard banner of iOS 14 and later makes silent reads visible).

### Copying into other apps, SMS, and non-Apple recipients
**Unmeasured, not claimed.** Whether another messenger, an email or the SMS fallback
keeps the variation selectors is not known; Notes on one phone kept them exactly (§1). Supplementary-plane code
points (240 of the 256 alphabet characters) in a concatenated SMS are a plausible
loss (inferred). Stypo is for iMessage between Apple devices running Stypo.

### Editing, forwarding and quoting
**verified** that editing the text after `insertText` can erase the whole run (one
backspace took the field from 187 UTF-16 units to 6). Editing a sent message,
forwarding it, replying with a quote, and what a recipient's keyboard or
autocorrect does to a pasted copy have not been measured. A truncated message
(a bubble over 4 000 units, which collapses) reads as "cut short", not as a
message that is not Stypo; this is by design and shows the recipient that a message
existed (`spec/text-layer.md` section 5).

### Accessibility and previews
**verified** that the accessibility label of a bubble carries every variation
selector (3 964 of them in the longest whole bubble). **verified** (banner on both
phones, Show Previews at Always and When Unlocked, 2026-11-08) that a banner of a
short message (92 selectors) reads as plain text, and that a banner of a very long
one (3 964 selectors) shows only the cover's first word and then stops, with no
mark: on the receiver's screen that is a **visible sign of a long secret** to
anyone who sees the banner, and a short secret has no such sign. The cutoff between
those two sizes was not measured. **Unmeasured:** what VoiceOver says for a
received bubble and whether it reads each selector out. What a lock-screen
preview shows was not measured (skipped by the owner's decision of 2026-11-08, on the design session's recommendation) and is unknown.

### Metadata about the conversation
- iMessage routing metadata (who sent what to whom, when).
- The fact that two people are exchanging messages that carry a run of invisible
  characters at all. (In Stypo this is visible in the message itself, §3
  "Detection".)
- Timing analysis on message exchange.

### Cryptanalysis of AES-GCM, PBKDF2, HMAC-SHA256, HKDF-SHA256
We assume the underlying primitives are sound.

## 4. Guarantees per mode

|                                                   | Open mode | Stealth v1 |
|---------------------------------------------------|-----------|------------|
| Confidentiality of the secret                     | ❌ none   | ✅ AES-256-GCM |
| Authenticity of the secret                        | ❌ none   | ✅ GCM tag |
| Hides the secret's length                         | ❌ exact, in clear | ⚠ to a 64-byte bucket (`50 + 64k` characters in the run) |
| Hides Stypo-specific markers (magic, header)      | ❌ `STYP` in clear | ✅ no magic, no fixed bytes |
| Hides "this message carries a run of hidden characters" | ❌ | ❌ a one-line scan finds it |
| Hides the cover's own text                        | — it is the message | — it is the message |
| Survives iMessage between Apple devices           | ✅ verified (byte for byte, iOS 26.7.2, 27.0 sim, 27.2) | ✅ same |
| Survives editing after it was added               | ❌ verified (backspace erased the run) | ❌ same |
| Survives a collapsed bubble (over 4 000 units)    | ❌ cut at 499 units, reported as cut | ❌ same |
| Survives SMS, other messengers, copy to other apps | unmeasured (Notes on one phone: exact) | same |
| Survives device compromise                        | ❌        | ❌ |

### When the stealth-mode guarantees apply

The "Stealth v1" column applies only when an outgoing send actually takes the
stealth code path. Three independent values decide that: the chat's password,
the user's encryption toggle and the Pro entitlement. They can disagree, and
Stypo composes them into the family's typed `EncryptionState` (the same type as
Stiger's and Stecho's) with one rule: **only `.ready` (Pro, encryption on, a
password for this chat) sends stealth; every other state sends open, and the
composer says so** — a button that reads "Add unencrypted", a banner, or a
one-shot confirmation for a user whose Pro has lapsed with a password still
saved. Nothing auto-mutates one value to "fix" another.

**Saved passwords.** Each chat has its own; the user decides on every send and
every typed reveal whether to keep it ("Save for this chat"). Kept passwords
live in one Keychain item (`*ThisDeviceOnly`), with which chat each is for. A chat
is identified by the set of remote participant UUIDs Messages gives the
extension; Stiger measured them to be replaced when the app is installed again
over itself, so a chat binding is a hint and not a key (Stiger
`docs/experiment-participant-ids.md`; **not re-measured in Stypo**). The reveal
makes one automatic attempt with the chat's password (or none, which reads an
open message) and offers the other saved passwords in a menu, one attempt per pick.

## 5. Trust assumptions

- The user's password is high entropy and not reused from a leaked corpus. The
  app shows a strength colour and does not enforce a minimum.
- The user shares the password through a channel Stypo does not see (in person,
  another messenger, paper). "Pair in person" exchanges one by QR code.
- iOS Keychain on a non-jailbroken device is treated as confidential storage.
- Apple's CryptoKit and CommonCrypto implementations of AES-GCM, HMAC-SHA256,
  HKDF and PBKDF2 are correct. `SecRandomCopyBytes` is a CSPRNG.
- iMessage delivers the text unchanged between Apple devices (verified on the
  versions listed in §1; other versions are assumed, not measured).

## 6. How to verify

The protocol is in [`spec/`](spec/README.md): `text-layer.md` (the alphabet, the
extraction rule, the placement, the cap), `open-v1.md` and `stealth-v1.md`. The
implementation is split across:

- `StypoCore/TextCarrierCodec.swift` — bytes to variation selectors, extraction
  (the longest run), placement, the cover rules
- `StypoCore/TextStegoMarker.swift` — header framing and the HKDF/HMAC derivations
- `StypoCore/TextStegoEngine.swift` — encode and decode of both modes, the cap, the bucket
- `StypoCore/AESHelper.swift` — AES-GCM and PBKDF2 wrappers
- `StypoCore/TextCompose.swift`, `StypoCore/TextReveal.swift` — what the composer and the reveal screen ask of the engine

A reference decoder written from the spec alone is in
`spec/reference/python/stypo_decode.py`; the Swift engine reads its test vectors
and the Python decoder reads the vectors the Swift engine writes
(`CrossImplVectorsTests`, `spec/test-vectors/`). If your decoder disagrees with
Stypo on a vector, the spec is wrong — please report it.

## 7. Known weaknesses (acknowledged, not fixed)

1. **Detectability.** §3. There is no layer to fix it with; spreading the run
   across the text would, by inference, change nothing for a scanner that looks
   for the code points (`docs/design.md` section 3).
2. **The run's position is fixed** (end of the first word). A scanner built for
   Stypo can look only there.
3. **Open mode exists in the same UI as stealth mode, and carries a fingerprint.**
   A person who forgets the password, or whose Pro lapsed, sends open (the
   composer says so on the button, in a note and, for a lapse, in a dialog), and
   the `STYP` magic in that message names the app for everyone in the chat.
4. **No forward secrecy.** A password leak retroactively decrypts every earlier
   message sent under it (per chat, §4 "Saved passwords").
5. **Per-chat passwords, distributed by hand.** Each chat has its own password, so
   one leaked or coerced password opens one chat, not every correspondent's.
   Distribution is manual: in person through QR pairing (which agrees a new
   128-bit password every time) or through a channel the user trusts. What it does
   not change, and what it adds:
   - Someone holding the unlocked phone, with the biometric lock off (the default)
     or knowing the passcode, opens with one drag every chat whose password is
     saved. "Save for this chat" off keeps a password out of the phone; the cost is
     typing it on every reveal.
   - The saved list is on-device metadata: how many passwords, when each was saved,
     and any name the user gave it ("Lawyer"). A name is optional: when a new
     password would be saved, a popup asks whether to keep it, with an empty
     "Name (optional)" field. The list sits behind the biometric lock with the rest
     of Settings, which falls back to the passcode.
   - Stypo cannot show which chat a password belongs to (Messages gives no names),
     and the binding may be lost on reinstall (§4 "Saved passwords"); the reveal
     makes one attempt with the chat's password and leaves the others to a menu.
6. **Length to a 64-byte bucket**, and exact length in open mode (§3).
7. **PBKDF2, not Argon2id.** PBKDF2-SHA256 at 600 000 iterations is the same choice as
   Stiger's and Stecho's; it is not memory-hard. **Inferred:** a determined attacker
   with GPUs is helped less by a long random password than by a short one, which is
   why "Pair in person" agrees 128 random bits.
8. **Truncation tells the recipient that a message existed.** A cut run is reported as
   cut, not as nothing (the price of telling the person to ask again).
9. **Editing after insertion destroys the message** (verified), and the extension can
   only say so; it cannot prevent the edit.
10. **iMessage only.** Other transports are unmeasured. Reading by paste exposes the
    message on the pasteboard (§3); the drag is the primary read route.
11. **Some numbers are proposals, not signed off:** the `STYP` magic, the 64-byte
    bucket and the `stypo-v1-header` domain string. The cap (3 600 units) and the
    body limit (2 000 bytes) are the owner's decision, 2026-11-08.

## 8. History

- **2026-11-08.** First version, written with the first design of the product,
  before any copy claims anything: the format and its reference decoder
  (spec), the read-path measurements (simulator and two phones), the engine,
  the extension and the container app. No App Store build exists yet.
- **2026-11-09.** Russian TL;DR added after the owner signed the English off,
  following Stiger's document. It says what the English says and no more; the
  English stays the text to cite if the two ever differ.
