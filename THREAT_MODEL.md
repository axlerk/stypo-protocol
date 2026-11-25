# Stypo — Threat Model

**Status:** TestFlight beta, not yet on the App Store. The text describes
the current code, in which Stypo is free and every feature is on for
everyone, and says, in the place where it matters, where the latest
TestFlight build (2026-11-11) is behind it. Formats: `open-v1` and
`stealth-v1`; some of their constants may change before 1.0 (the
specification says which). Last checked against the code on 2026-11-20.

This document says what Stypo protects, what it does not, and how we know.
Read it before you trust the app with anything that matters.

If the app does less than this document says, the app is wrong. If the
document says more than the code or a measurement backs, the document is
wrong. If a decoder written from the specification disagrees with the app,
one of the two has a bug. In each case, please tell us (§6).

The format, a reference decoder and test vectors are public:
<https://github.com/axlerk/stypo-protocol>. Every figure this document
relies on is in the text, with its sample size and date. The record named
beside it is where the run is written down; the records live in the app's
source repository, which is private. A dagger (†) marks what we have not
checked ourselves; §5 lists it all.

## TL;DR

**English.**

- A short text is encrypted and hidden as a run of invisible characters
  inside an ordinary text message that you write, sent through iMessage.
- With a password, nobody reads the message without it (AES-256-GCM, key
  from the password by PBKDF2-SHA256, 600 000 iterations). The password is
  the whole defence, so make it a long one.
- Stypo is the easiest member of its family to detect. A one-line scan for
  those characters finds the run, and its length gives away the size of the
  message to within 64 bytes. The password hides what the message says, not
  that it is there.
- An unlocked phone in someone else's hands gives everything away: saved
  passwords open the messages, and spyware sees what you see. A password
  that leaks opens every earlier message sent under it.
- Without a password (open mode) anyone can read the message, with Stypo or
  without it. That is for jokes and love notes, not for privacy.

**По-русски.**

- Короткий текст шифруется и прячется цепочкой невидимых символов внутри
  обычного текстового сообщения, которое ты пишешь сам; оно уходит через
  iMessage.
- С паролем сообщение без него не прочитать (AES-256-GCM; ключ получается из
  пароля через PBKDF2-SHA256, 600 000 итераций). Вся защита — в пароле, так
  что выбирай длинный.
- Stypo обнаружить проще, чем любое другое приложение семейства. Цепочку
  невидимых символов находит проверка в одну строку, а по её длине виден
  размер сообщения с точностью до 64 байт. Пароль скрывает, что написано, но
  не то, что сообщение есть.
- Разблокированный телефон в чужих руках ничего не скрывает: сохранённые
  пароли открывают сообщения, а шпионская программа видит то же, что и ты.
  Если пароль утёк, им откроются и все сообщения, отправленные с ним раньше.
- Без пароля (открытый режим) сообщение прочтёт кто угодно, со Stypo или без
  него. Такой режим — для шуток и любовных записок; для защиты переписки он
  не годится.

## 1. What Stypo does

Stypo hides a short text (about 1 700 bytes at most) in an ordinary iMessage
text message. You write a visible text. Stypo writes the hidden message as a
run of invisible characters (variation selectors, one byte per character)
after the first word of your text, and puts the finished text into Messages'
own field for you to send. The recipient drags the bubble into Stypo, or
copies and pastes it there, and reads the message.

**How much fits.** The whole text, visible part included, may be 3 600
UTF-16 units: Messages collapses a bubble past 4 000 (measured, §3.4), a
collapsed bubble loses the run, and the cap sits 10 % under that. The app
counts two units for every hidden byte, so by that rule 1 726 bytes of
message fit in stealth mode beside a visible text of up to 44 units, and 64
fewer for every further 128 units of visible text. That is about 1 700 Latin
letters or 850 Cyrillic ones. The format's own limit of 2 000 bytes is never
reached.

Do not edit the text after Stypo has added it: one backspace can take the
whole run with it (§3.4).

Two modes share the layer (`text-layer.md`):

- **Open mode** (`open-v1.md`): no password. The run starts with the `STYP`
  marker, a version and the exact length.
- **Stealth mode** (`stealth-v1.md`): a password both people know. The run
  is a random salt, a keyed marker and the encrypted text, padded to a
  multiple of 64 bytes. No marker, no length in clear.

## 2. What it protects

### 2.1 The content

The message is encrypted with AES-256-GCM before it is hidden. The key comes
from your password through PBKDF2-HMAC-SHA256 with 600 000 iterations and a
random 16-byte salt for each message (`stealth-v1.md` §3). Without the
password the hidden bytes look random.

**The password is the whole defence.** The format and the app are public, so
whoever holds a text can try passwords as fast as PBKDF2 runs, and graphics
cards run it quickly. A short or reused password turns a saved text into a
readable one; the app colours the password field by strength and refuses
nothing. For scale: six lowercase letters are about 3 × 10^8 possibilities
(28 bits), four random words from a list of 7 776 about 4 × 10^15 (52 bits).
How many guesses a second an attacker manages depends on their hardware; we
have not measured it†. "Pair in person" avoids the problem: one phone makes
a random 128-bit password and hands it to the other through two QR codes, so
nobody invents or types one.

Why PBKDF2 and not Argon2id, which would cost an attacker more per guess:
PBKDF2 is the only password function in Apple's SDK†, and Argon2id would put
third-party cryptography into the app and into every reference decoder.

### 2.2 Integrity, and one answer for every failure

The GCM tag covers the encrypted message. Change one hidden bit and the
check fails. A wrong password, a message that was changed on the way and a
text with no message all get the same answer, on purpose: the screen does
not show whether a particular text holds something you cannot open. One
exception, on purpose: a run that was cut short is reported as cut, so the
recipient can ask for the message again.

### 2.3 No app marker in the stream

A stealth message has no magic bytes, no version and no length in clear. It
is a random salt, a keyed marker that differs for every message, and
ciphertext (`stealth-v1.md` §2). A scanner that looks for a known signature
has nothing to match. This is protection against signature scanners, not
against statistics (§3.1).

### 2.4 Open mode

Open mode needs no password. Anyone with Stypo, or with the specification
and its reference decoder, reads the message. The run starts with the `STYP`
marker, which names the app on purpose. An open message also points at the
encrypted ones next to it: same chat, same app. It is for jokes and love
notes, never for anything that matters, and the composer says so every time
it is about to send one.

## 3. What it does not protect

### 3.1 That a text carries a message

This is Stypo's main limit, and nothing in the design tries to fix it.

- **A scan finds the run.** Variation selectors are ordinary Unicode code
  points, and looking for a run of them takes one line of code. Ordinary
  text carries one or two beside an emoji†; Stypo's shortest stealth run is
  114 characters (`stealth-v1.md` §7), a typical one several hundred.
- **The run is always in the same place**, right after the first word
  (`text-layer.md` §3). A scanner built for Stypo does not even need to
  search.
- **Your visible text gives no cover.** It is sent as you wrote it; the run
  is the only part of the message that is not ordinary text.

Stiger and Stecho embed in a way meant to be hard to tell from an ordinary
file. Stypo does not, and will not. There is no table of detector scores
here because none is needed: finding the run is certain.

### 3.2 The size of the message

Stealth mode pads the message to a multiple of 64 bytes, so a run is `50 +
64k` characters long (`stealth-v1.md` §7). Whoever finds it counts it and
knows the size to within 64 bytes. Open mode states the exact length.

### 3.3 The text and the "From Stypo" label

Messages puts no "From Stypo" label on a text bubble, on the sender's phone
or the recipient's (n = 1 per view, 2026-11-08, `experiment-read-path.md`).
That is why Stypo has no "Copy instead of send": there is no label for it to
avoid. What a text can show instead (same record, one run per case):

| Where | What shows |
|---|---|
| A notification banner, short message (92 hidden characters) | The visible text, as for any message |
| A notification banner, very long message (3 964 hidden characters) | The first word, then nothing: a visible sign that something long follows |
| VoiceOver | The bubble's accessibility label holds every hidden character; what is spoken was not measured† |
| The lock screen | Not measured† |

### 3.4 Transport

Stypo needs every character of the run to arrive, in order.

| Case | Result | n |
|---|---|---|
| A received bubble dragged into Stypo | read exactly | 12 of 12 |
| Copy, then paste, when iOS shows its paste prompt | read exactly | 7 of 8 on the phones, refused once without a prompt; the simulator returned nothing, 6 of 6 |
| A text of up to 4 000 UTF-16 units | the bubble is drawn whole | iOS 26.7.2, 27.0, 27.2 |
| A text of 4 001 units or more | the bubble is collapsed and drags as its first 499 units; Stypo reports the message as cut | same |
| One backspace in Messages' field after the text was added | the whole run was deleted | 1, simulator |
| Two adds before one send | one bubble with two runs, which reads as damaged; the app asks before a second add in the same chat (not yet in the latest TestFlight build) | 1, simulator |
| A copied bubble pasted into Notes | the message survived | 1, iPhone 12 mini; three runs on the iPhone 15 Pro were inconclusive |

Measured 2026-11-08 to 12 on an iPhone 12 mini (iOS 26.7.2), an iPhone 15
Pro (iOS 27.2) and the iOS 27.0 simulator (`experiment-read-path.md`). SMS,
recipients outside Apple devices, other messengers, forwarding, quoting and
editing a sent message were not tried†. Stypo is for iMessage between Apple
devices.

### 3.5 Your phone

- **Saved passwords.** Each chat has its own password, and keeping it is
  your choice each time ("Save for this chat"). Saved ones sit, with the
  date each was saved and any name you gave it, in a Keychain item that
  never leaves this phone: no iCloud Keychain, no move to a new phone with a
  backup. It sits in a Keychain group that only Stypo and its extension
  share, so other apps cannot read it; forensic tools on a phone unlocked
  since it was switched on can†. Switching encryption off does not remove
  saved passwords; Forget in Settings → Saved Passwords does. Deleting the
  app leaves the item in place† until Stypo is installed afresh, which wipes
  it.
- **The Face ID lock** is off by default. Off, whoever holds the unlocked
  phone opens every chat that has a saved password by dragging a text into
  Stypo. On, the app asks for Face ID or the phone's passcode first: that
  stops a person who does not know the passcode, and nobody else. The lock
  is the app's own check: the Keychain item is not tied to Face ID, and the
  phone hands it to the app whenever it is unlocked. In the latest
  TestFlight build (2026-11-11) the lock also has gaps when it is on: a link
  into the app opens Saved Passwords and the guide without asking, the About
  tab opens the guide the same way, and the guide's switch turns the lock
  off, again without asking. The next build closes them.
- **Leaving the app.** In the latest TestFlight build (2026-11-11) nothing
  covers the screen when you leave: the app switcher keeps a picture of it,
  a revealed message is still there when you come back, and it can still be
  open when you use the extension in another chat. The next build covers the
  reading screen and, with the Face ID lock on, clears the message and locks
  again (checked in a simulator, 2026-11-15/16; not on a phone†). The
  composing screen is not covered in either.
- **Keyboard.** A third-party keyboard with Full Access can send what you
  type to its developer. Password fields are marked secure, which should
  bring up the system keyboard†; the two message fields are ordinary ones.
  The secret field offers suggestions and autocorrection, as the cover does
  (the owner's decision, 2026-11-24: with them off in one field only, the
  suggestion bar came and went as you moved between the fields and the form
  jumped). So the system keyboard may learn words of a secret and offer them
  later, in other apps too†.
- **Drafts.** Nothing unsent is written to the phone. Collapsing the panel
  keeps an unfinished message in memory, and with the Face ID lock on it asks
  again before it shows. When Messages closes Stypo (another app, the Home
  screen, the lock), the message is gone. Drafts that an older build kept
  are deleted, with their key, the first time Stypo opens after the update.
- **Clipboard.** "Paste instead of drag" uses Messages' own Copy, which
  Stypo does not control: that copy can reach your other devices through
  Universal Clipboard† and stays until something replaces it. Dragging never
  touches the pasteboard.
- **Spyware and other eyes.** Anything that reads the screen or the keyboard
  sees the message in clear. So does a person looking over your shoulder, a
  screenshot the recipient takes, or VoiceOver reading the text aloud. A
  jailbroken phone protects nothing.
- **Coercion.** Someone who can make you unlock the phone or say the
  password gets the messages. There is no decoy password and no hidden
  second mode.

### 3.6 The recipient's phone and backups

Everything in §3.5 is true of the other phone too, and a careless or
unfriendly recipient is beyond what an app can fix. The text stays in both
Messages histories and in their backups; in iCloud that means Apple's
storage, under keys Apple holds unless Advanced Data Protection is on†.
Saved passwords do not travel with a backup to another phone, but a text
from a backup plus a password learned some other way is a readable message.

### 3.7 Who talks to whom

Stypo changes nothing about the conversation around the text: who wrote to
whom and when is as visible as for any iMessage, and so is the fact that two
people keep exchanging texts.

### 3.8 Past messages

There is no forward secrecy: a password that leaks opens every message ever
sent under it. Changing that would take a key exchange for every message,
which a text cannot carry. Each chat has its own password, so a leak costs
one chat. If you suspect one, set a new password; it protects what comes
next and nothing sent before.

### 3.9 Network requests the app makes

Stypo has no server and no accounts, and its code calls no analytics or
tracking service: it imports Apple's frameworks, nothing else (read
2026-11-20). The app makes no network
request of its own, and a revealed message is plain text: a link in it opens
nothing. In the latest TestFlight build (2026-11-11) links are still
detected: a tap opens one in a Safari sheet, and a long press may load a
preview from the sender's address†. It does show maps, and maps come from
Apple.

**A map reaches Apple Maps only when you ask.** When a revealed text holds
coordinates (an attached place, `geo:`, or a map link with coordinates in
it), the reading screen shows them on a card with a "Show map" button and a
Copy button. Nothing is requested before the person agrees: a tap on "Show
map" and a tap on the `geo:` link in the text ask the same question (owner,
2026-11-24: one consent for the link and the button). After "Show map"
Apple's map servers receive the area around the coordinates, from the
recipient's IP, at that moment; the message itself is not sent. "Always show
maps" on that question, or the switch in Settings, draws the map as soon as
a message is read. Copy puts the card's digits on this device's pasteboard
only (not Universal Clipboard) and sends nothing. Nothing in the reveal opens
in an in-app browser. Once the map is shown, only the "Open in Maps" button
hands the place on (owner, 2026-11-24): a tap on the map or on the `geo:`
link does nothing more. A Messages extension cannot open another app
(`extensionContext.open` always opened Stypo itself, iPhone 17 simulator,
iOS 27.0, 2026-11-24), so the button opens Stypo with
`stypo://map?ll=<lat>,<lon>` and Stypo opens a `maps.apple.com` address it
builds from those two numbers (`PlaceHopLink`). Stypo shows for a moment on
the way. The app accepts nothing else on that link, so the hop cannot open an
address from a message. A map link from Google, Yandex or Waze opens Apple
Maps at its coordinates, never the sender's address. Any other kind of link
does nothing.

**Attaching a place talks to Apple too, after the same question.** "Pick on
Map" asks the reader's question first, with the same "Always show maps"
setting; before the answer no map view exists and nothing is searched
(owner, 2026-11-24). Once the picker is open it loads Apple's map tiles for
the area shown, and typing in its search field sends what is typed to Apple.
"Current location" shows no map: it asks for permission the first time,
then makes one location request through Core Location. What Core Location
sends to Apple for that one fix is not documented: Apple's pages say Location
Services uses GPS, Bluetooth and "crowd-sourced Wi-Fi hotspot and cell tower
locations", and that a device with Location Services on periodically sends
the locations of nearby hotspots and towers to Apple, anonymously (Apple,
Location Services & Privacy, apple.com/legal/privacy/data/en/location-services,
read 2026-11-24); they say nothing about a single app's request. All of this
comes from the sender's IP. Stypo itself sends the coordinates nowhere: they
become ordinary text in the hidden message.

**In open mode a place is as public as the rest of the message** (§2.4):
anyone with Stypo, or with the specification and its reference decoder,
reads the coordinates. For a message that *is* a place, the area Apple sees
after "Show map" is most of what it says; to keep a place away from Apple,
do not tap "Show map", or write it as plain words. TestFlight build 6
(2026-11-21) has no place or map at all.

## 4. At a glance

### 4.1 Guarantees per mode

|  | Open mode | Stealth mode |
|---|---|---|
| Keeps the message unreadable | ❌ | ✅ AES-256-GCM, as strong as the password (§2.1) |
| Notices any change to the message | ❌ | ✅ GCM tag (§2.2) |
| No app marker in the hidden stream | ❌ `STYP` | ✅ (§2.3) |
| Hides the size of the message | ❌ exact, in clear | ⚠ to within 64 bytes (§3.2) |
| Hides that the text carries a message | ❌ (§3.1) | ❌ a one-line scan finds it (§3.1) |
| Hides which app sent it | ❌ `STYP` names it | ⚠ no label on a text (§3.3), but the run's place and shape are Stypo's (§3.1) |
| Survives iMessage between two iPhones | ✅ measured (§3.4) | ✅ same |
| Survives editing, a collapsed bubble | ❌ (§3.4) | ❌ (§3.4) |
| Protects earlier messages if the password leaks | — | ❌ (§3.8) |
| Holds on an unlocked or compromised phone | ❌ (§3.5) | ❌ (§3.5) |

### 4.2 Who sees what

| Who | What they see | What stays protected |
|---|---|---|
| **Someone who picks up your unlocked phone** | Stypo among the apps; a text message that looks ordinary in the chat, though a banner can give a long one away (§3.3); every chat with a saved password, if the Face ID lock is off (§3.5) | Stealth messages whose password is not saved |
| **Someone with a copy of the text** (a backup, a forward, the other phone) | Open messages in full. With a one-line scan: that a message is there, and its size to within 64 bytes (§3.1, §3.2) | Stealth content, as long as the password holds (§2.1) |
| **Someone with extraction tools and the unlocked phone** | The saved passwords†, so every chat that has one, earlier messages included (§3.5, §3.8); the Messages history | Chats whose password was never saved, as long as it is strong |
| **Spyware on the phone** | What you see and type | Nothing (§3.5) |

Stypo keeps what a short text says, and is the simplest way into the family.
It makes no attempt to hide that something is there: use it where that does
not matter.

### 4.3 When a message goes out in stealth mode

Two things have to hold: encryption switched on, and a password for this
chat. Otherwise the message goes out open, and the composer says so before
you send. Encryption starts off, so a new user sends open until they turn it
on. The app never changes one of the two to make up for the other. In the
latest TestFlight build (2026-11-11) Pro is still a third condition; the app
became free after it.

- **One password per chat.** A chat is recognised by identifiers that
  Messages gives the extension. They changed when the app was installed
  again over itself, and survived a TestFlight update (measured for Stiger:
  developer installs on iOS 27.2 and 26.7.2, the update on iOS 27.2,
  2026-11-02/03; not repeated for Stypo†). So the link between a saved
  password and its chat can break, and the app does not rely on it alone.
- **Reading tries saved passwords.** A reveal tries the chat's own password
  first, then up to seven other saved ones; eight tries took 0.75 s on a Mac
  (2026-11-12), and a phone was not timed†. So a message under any password
  saved on your phone can be opened in any chat.
- **Reading never moves a chat to another password.** If another saved
  password opens a message, the reading screen says so, and in a chat with
  no password it offers a switch, off by default, to keep that one. Only you
  change a chat's password. The latest TestFlight build (2026-11-11) is
  older than this and the bullet above: it makes one automatic try, with the
  chat's own password, leaves the other saved ones to a menu, and has no
  switch.

## 5. Assumptions and what is unverified

Stypo's claims hold if your password is long and used nowhere else; the
other person got it in person ("Pair in person") or over a channel you
trust; neither phone is jailbroken or runs spyware; Apple's cryptography
(CryptoKit, CommonCrypto, `SecRandomCopyBytes`) is correct and the
primitives hold; and iMessage keeps delivering the text unchanged (§3.4),
which is observed behaviour, not Apple's promise.

**† Not checked by us.** Recalled, assumed, inferred, or measured for a
sibling only:

- that iOS keeps Keychain items after an app is deleted, and that extraction
  tools reach them (§3.5): recalled;
- that iOS shows its own keyboard for a secure field (§3.5): set in the
  code, not tested;
- that Apple's SDK has no password function besides PBKDF2 (§2.1): checked
  once, against the iOS 27.2 SDK on 2026-11-10, and no record was kept; how
  fast an attacker guesses: not measured;
- how iCloud protects Messages and backups (§3.6): recalled, not read at the
  source;
- that a local-only pasteboard item stays off Universal Clipboard, and that
  a copy made in Messages travels through it (§3.5): the first is a flag set
  in the code, neither was measured;
- what the app switcher shows on a real phone (§3.5): simulator only;
- the chat identifiers after a reinstall or an update (§4.3): measured for
  Stiger, which shares the code, and for a TestFlight update only;
- how many variation selectors ordinary text carries (§3.1): expected to be
  one or two, no corpus was measured;
- what VoiceOver speaks, the lock-screen preview, and where between 92 and 3
  964 hidden characters a banner starts to cut (§3.3);
- SMS, recipients outside Apple devices, other messengers, forwarding,
  quoting, editing a sent message (§3.4); most of Stypo's characters lie
  outside the basic plane of Unicode, which a long SMS may not keep:
  inferred; a collapsed bubble copied on a phone; iOS versions other than
  those of §3.4, the Mac and the Watch;
- what a long press on a detected link loads inside Messages (§3.9): not
  measured.

## 6. How to verify and where to report

Everything needed to check Stypo's claims about the format is in
<https://github.com/axlerk/stypo-protocol>:

| File | What it holds |
|---|---|
| `text-layer.md` | Bytes as invisible characters, how a decoder finds the run, where it is placed, the size limits |
| `open-v1.md`, `stealth-v1.md` | The two modes: framing, key derivation, AES-256-GCM, the padding |
| `reference/python/` | A reference decoder written from the specification alone |
| `test-vectors/` | Messages, passwords and the expected results |

The app's engine reads the reference decoder's vectors, and the reference
decoder reads the vectors the app writes. A decoder is about thirty lines
for open mode; it can open a text from your own chat without Stypo.

Found a gap between this document and the app, or between the app and the
specification? Open an issue at
<https://github.com/axlerk/stypo-protocol/issues>. For an attack on the
format, write first to hello@onegoodman.studio with `[SECURITY]` in the
subject.

## 7. History

| When | What changed | What it means for old texts |
|---|---|---|
| 2026-11-24 | One question before any map: the `geo:` link in the text asks like "Show map", and "Pick on Map" asks before its map loads; Copy for the coordinates; no in-app browser; "Open in Maps" (the button only) hops through the app with `stypo://map?ll=` | The format did not change |
| 2026-11-24 | The secret field has the cover's suggestions and autocorrection | Nothing changes for texts already sent; words typed into a secret from now on may be learned by the keyboard |
| 2026-11-21 | A place can be attached to the hidden message (`geo:` coordinates in its text); reading shows a place on a card and asks Apple Maps for the map only after "Show map" | The format did not change: a place is text. TestFlight build 6 (2026-11-21) has neither |
| 2026-11-21 | Unsent messages are no longer kept on the phone | Drafts from older builds are deleted on update |
| 2026-11-15 | Stypo became free: stealth mode, saved passwords and pairing need no purchase | The format did not change. The latest TestFlight build (2026-11-11) still asks for Pro |
| 2026-11-11 to 13 | Reading tries up to eight saved passwords and never changes a chat's password; the app asks before a second add | The latest TestFlight build (2026-11-11) has none of the three |
| 2026-11-08 | First version of the format and of this document | — |

## Glossary

| Term | Meaning |
|---|---|
| AES-256-GCM | The cipher: encrypts the message and detects any change to it |
| Carrier | The text a message is hidden in |
| Forward secrecy | A leaked key does not open earlier messages. Stypo does not have it (§3.8) |
| Open mode / stealth mode | Without a password, readable by anyone, with Stypo or without it / with a password, encrypted |
| PBKDF2 | Turns a password into a key, slowly on purpose (RFC 8018) |
| Run | The unbroken sequence of invisible characters that holds the message |
| Steganalysis | Detecting that something is hidden, without reading it |
| UTF-16 unit | How Messages counts the length of a text; most letters are one unit, an emoji is two or more |
| Variation selector | A Unicode character that normally picks the look of the character before it and draws nothing itself. Stypo uses 256 of them as bytes |
| Visible text | What you write yourself; the hidden message rides inside it |
