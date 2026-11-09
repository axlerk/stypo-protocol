# Stypo: Privacy Policy

_Last updated: 9 November 2026_

Stypo is an iOS app and iMessage extension that hides a short text inside
an ordinary text message, using invisible characters and, with a password,
AES-256-GCM encryption. Everything happens on your device. This document
describes what data Stypo does and does not collect.

## TL;DR

- Stypo has **no servers**, **no accounts**, **no analytics**,
  **no advertising**, **no third-party tracking SDKs**.
- Everything you create (secrets, cover texts, passwords) stays on your
  device.
- Stypo makes **no outbound network requests** of its own.

## Data we collect

**None.** Stypo does not transmit any personal data to its developer or to
any third party for our own use.

## Data stored on your device

| What | Where | Encrypted at rest |
|---|---|---|
| Saved chat passwords (only if you choose to save one) | iOS Keychain | Yes (Keychain) |
| App settings (encryption on/off, biometric lock on/off, etc.) | App Group `UserDefaults` | No |
| Drafts you save in the extension (a cover text and a secret) | App Group container | Yes: AES-256-GCM under a random key kept in the Keychain, this device only (never in backups or iCloud Keychain). Deleted automatically after 72 hours |

Stypo does not keep a copy of the messages you send or receive. The finished
message is handed to Messages, which stores and delivers it. A secret you
read is shown on screen and not stored.

Removing the app removes everything in the table above.

## Outbound network requests

**None initiated by Stypo.** Stypo does not call any server, does not
refresh any catalog, and does not phone home for any feature. The message you
send leaves your device only through Apple's iMessage service, which is
operated by Apple and outside Stypo's control.

Stypo never uploads your secrets, cover texts, passwords or any other
user-generated content to any server.

Two things you start yourself do reach the network, and neither goes through
a Stypo server. A link you tap (the Terms of Use, this Privacy Policy, the
website, the specification, or a web link that appears inside a secret you
have read) opens in Safari or in an in-app Safari view, and Safari makes that
request to the site of the link. Purchases go through Apple (see below).

## Pasteboard

Stypo reads the pasteboard only when you tap the paste button in the
reveal screen ("Paste instead of drag"). It never reads it in the
background. iOS may show its own "Allow Paste" prompt.

## Camera

Stypo requests camera access only when you scan a partner's QR code to
share a password. The image is processed on the device to read the code
and is not stored or sent anywhere. If you deny access, you can still type
a password by hand.

## Face ID / Touch ID

Stypo uses biometric authentication only to gate access to settings and
saved passwords on your device. Authentication happens entirely through
Apple's `LocalAuthentication` framework; Stypo never sees your biometric
data.

## Purchases

In-app purchases (Stypo Pro monthly, yearly, lifetime, and the tip) are
processed by Apple via StoreKit. Stypo sees only an anonymous entitlement
flag indicating whether you have an active purchase. We do not receive your
name, email, payment details, or App Store account.

## What Stypo cannot protect against

For completeness, and because Stypo is a security-adjacent tool, the threat
model is documented in detail at
<https://github.com/axlerk/stypo-protocol/blob/main/THREAT_MODEL.md>.
Short version: with a password, Stypo protects what a message *says*
(AES-256-GCM, PBKDF2-SHA256 with 600,000 iterations). It does **not** hide
that a message carries something: anyone who scans a text for invisible
characters can find the hidden run. Without a password (open mode) anyone
with Stypo or the public specification can read it. It also does not survive
a compromised device (forensic extraction, spyware).

## Children

Stypo is not directed at children under 13 and does not knowingly collect
data from them.

## Changes to this policy

Updates will be published at this URL with a new "Last updated" date.

## Contact and data controller

Privacy questions, deletion requests, or anything else:

**Individual Entrepreneur Pavel Khudiakov** (Tbilisi, Georgia)
Email: hello@onegoodman.studio

The full registered address is on file with the Apple App Store and is
disclosed to regulators on request.
