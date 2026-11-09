# Stypo: Support

## What is Stypo?

Stypo is an iOS app and iMessage extension that lets you hide a short text
inside an ordinary text message. The recipient sees the message you wrote;
the secret is carried by invisible characters after its first word. Your
recipient needs Stypo to read it. If you set a password, the secret is
encrypted, and you both need the password.

## Quick start

1. Install Stypo from the App Store.
2. Open Messages, tap the apps drawer, and choose Stypo.
3. Tap **Hide a text**. Write the message everyone will see, then type the
   secret.
4. (Optional, recommended) Turn on encryption in the Stypo app and set a
   password you and your partner already share.
5. Add the secret to the message, then send it as usual. Do not edit the
   message after Stypo has added the secret: editing can erase it.
6. The recipient touches and holds the received message, drags it into the
   Stypo extension (or taps Copy, then uses the paste button in Stypo), and the
   secret appears.

For the byte-level format and an independent Python reference decoder, see the
specification in the public repository,
<https://github.com/axlerk/stypo-protocol>.

## Frequently asked questions

**Q: Does Stypo have my secrets?**
No. Everything is computed on your device. Stypo has no servers and no
accounts.

**Q: What encryption does it use?**
AES-256-GCM with a key derived from your password via PBKDF2-SHA256
(600,000 iterations). Open mode (the free tier) does not encrypt: anyone with
Stypo, or with the public specification, can read the secret. Encryption
requires Stypo Pro.

**Q: Can someone tell a message has a secret in it?**
Yes. Stypo is the most detectable app of its family. The secret is carried by
a run of invisible characters, and anyone who scans the text for them finds the
run. Even with a password, the encryption hides what the message says, not that
it is there. Open mode is for fun, not for anything sensitive, and it also
reveals, by association, that other messages in the same chat may be
encrypted. The full threat model is published in `THREAT_MODEL.md` in the
public repository.

**Q: Does it work in SMS, WhatsApp, or on Android?**
Stypo is for iMessage. SMS and other apps may change or drop the invisible
characters, and an Android recipient cannot read the secret without Stypo.
Only iMessage has been tested.

**Q: Do screenshots carry the secret?**
No. A screenshot shows only the visible text.

**Q: How long can a secret be?**
It is a short text. The composer shows how many characters are left, and the
button stays off when the message is over the limit.

**Q: I edited the message and the secret is gone.**
Editing a message after Stypo has added the secret can erase it. Start over
and send it without changing the text.

**Q: I lost my password.**
We cannot recover it. The password never leaves your device, and without it
the secret is unrecoverable.

**Q: I'm in Russia and the App Store won't let me pay.**
All Pro features are unlocked automatically when your iPhone's primary system
language (iOS Settings → General → Language & Region → iPhone Language) is set
to Russian. The per-app language override (iOS Settings → Stypo → Language) is
intentionally **not** counted: only the system-level language unlocks free
Pro.

## Contact

**hello@onegoodman.studio**: bugs, feature requests, security issues. For
security issues, please prefix the subject line with `[SECURITY]`.

---

_Operated by Individual Entrepreneur Pavel Khudiakov (Tbilisi, Georgia)._
