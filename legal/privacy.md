# Stypo: Privacy Policy

_Last updated: 28 November 2026_

Stypo is an iOS app and iMessage extension that hides a short text inside
an ordinary text message, using invisible characters and, with a password,
AES-256-GCM encryption. Hiding and reading happen on your device. This document
describes what data Stypo does and does not collect.

## TL;DR

- Stypo has **no servers**, **no accounts**, **no analytics**,
  **no advertising**, **no third-party tracking SDKs**.
- Everything you create (secrets, cover texts, passwords) stays on your
  device.
- Stypo reaches the network only when you tap a link or use a map (see below).

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

Removing the app removes its settings and drafts. iOS may keep Keychain
items after an app is deleted; Stypo erases its saved passwords the next time
it is installed on this device. Until then they may stay in this device's
Keychain, where no other app can read them.

## Outbound network requests

**Stypo has no server and sends nothing on its own.** The message you send
leaves your device only through Apple's iMessage service, which Apple
operates. Stypo never uploads your secrets, cover texts or passwords
anywhere.

A few things do reach the network. Each happens only after you tap, and each
goes to the service named here, never to Stypo:

- **A link you tap** (the Terms of Use, this Privacy Policy, the website, the
  specification) opens in Safari or in an in-app Safari view.
- **Pick on Map**, when you attach a place: Stypo first asks, as it does
  before showing a map. Once you agree, Apple Maps loads the map you look at,
  and what you type in its search goes to Apple as you type. Its "My
  location" button shows where you are while the map is open.
- **Current Location**, when you attach a place: iOS asks your permission the
  first time, then gives Stypo your position once. Stypo writes it into your
  secret as coordinates and keeps no other copy.
- **Show map**, when you read a secret that has a place: Stypo asks Apple Maps
  for a picture of about one kilometre around it. Tapping the coordinates in
  the secret asks the same question. Until you agree, nothing is requested,
  unless you chose "Always show maps" on that question or turned on "Show
  maps without asking" in Settings. A map link from Apple Maps, Google Maps,
  Yandex Maps or Waze stays plain text; if it carries coordinates it gets the
  same card.
- **Open in Maps**, a button under the map once it is shown: Stypo opens for a
  moment and passes the place's coordinates to the Maps app, never the address
  of a link from another map site.

Any other web address inside a secret stays plain text and opens nothing.

Apple sees these map requests from your IP address, as it does for any app
that shows a map. To keep a place away from Apple, leave "Show maps without
asking" off and answer Cancel when Stypo asks. Copy, on the same card, puts
the coordinates on this device's pasteboard and sends nothing.

## Pasteboard

Stypo reads the pasteboard only when you tap the paste button in the
reveal screen ("Paste instead of drag"). It never reads it in the
background. iOS may show its own "Allow Paste" prompt. It writes to the
pasteboard only when you tap Copy on a place, and then only on this device,
not to your other devices.

## Camera

Stypo requests camera access only when you scan a partner's QR code to
share a password. The image is processed on the device to read the code
and is not stored or sent anywhere. If you deny access, you can still type
a password by hand.

## Location

The Messages extension asks for location access ("While Using the App")
only when you choose Current Location, or "My location" on the map, to attach
a place. Stypo puts the position into the secret you are writing and sends it
nowhere itself; it leaves your device only inside the message you send. The
app itself never asks for location. If you deny access, you can still pick a
place on the map.

## Face ID / Touch ID

Stypo uses biometric authentication only to protect settings, saved
passwords and, when you turn the lock on, the writing and reading of secrets
on your device. Authentication happens entirely through
Apple's `LocalAuthentication` framework; Stypo never sees your biometric
data.

## Purchases

Stypo is free and sells nothing: no in-app purchases, no subscription, no tips.

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
