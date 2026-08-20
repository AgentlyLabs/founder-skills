---
name: cold-email
description: Write, audit, and fix cold outbound email — targeted B2B outreach that actually reaches an inbox and earns a reply. Covers the three things that decide the outcome: sending-domain authentication (SPF, DKIM, DMARC, alignment, and the Google/Yahoo/Microsoft bulk-sender rules), the legal requirements that differ by jurisdiction (CAN-SPAM, GDPR/ePrivacy, CASL), and copy discipline measured against reply rate rather than open rate. Use this whenever the user is writing a cold email, outbound sequence, sales email, intro email to a stranger, investor or partnership outreach, or a follow-up; asks why their emails get no replies, land in spam, or bounce; asks about deliverability, warming up a domain, sending volume, or "am I blacklisted"; wants a draft critiqued, shortened, or rewritten; or asks whether they are allowed to email a list. Trigger even when they never say "cold email" — "help me reach out to this VP", "why is nobody responding to my outreach", "is this sequence any good", and "we're launching outbound next month" are all this skill.
---

# Cold Outbound That Reaches and Gets Replies

## What decides the outcome

Three independent systems have to succeed, in this order:

1. **Delivery.** An unauthenticated message never gets read, however good it is. This is
   deterministic, checkable, and the most common silent failure.
2. **Legality.** What you must include, and whether you may send at all, depends on where
   the recipient is. The US, EU/UK, and Canada have materially different regimes.
3. **The reply.** Copy craft, which is where nearly all published advice lives and where
   the least of it is verifiable.

Most outbound fails at (1) while the sender rewrites (3). So diagnose in order, and never
skip Step 1 because the copy looks like the interesting problem.

The discipline in this skill: **every recommendation names its mechanism, and metrics that
cannot be measured are called out rather than reported.** Open rates in particular are
close to meaningless now — see `references/deliverability.md`.

## Scope

This is for **targeted outreach at low volume**: a researched list where you can state,
per recipient, why you emailed that person. That is both the legally defensible posture
and the one that actually works — reply rate collapses as list size grows, because the
specific reason for the email is what earns the reply.

If the user wants high-volume untargeted blasting, say plainly that it will burn the
sending domain, and that the domain reputation damage is slow to reverse. Then help them
do the targeted version.

## Step 1 — Audit the sending domain before writing anything

Run this first, every time, even if the user only asked for copy help:

```bash
python3 scripts/check_domain.py example.com
```

It resolves SPF, DKIM (probing common selectors), DMARC, MX, MTA-STS and TLS-RPT, then
reports each as PASS / WARN / FAIL with the specific fix. Add `--json` for machine output,
`--selectors s1,s2` to probe custom DKIM selectors.

Interpret the result against `references/deliverability.md`, which has the actual provider
requirements — including the distinction almost everyone gets wrong: Google requires SPF
*or* DKIM from **all** senders, but SPF *and* DKIM *and* DMARC with alignment from **bulk**
senders (5,000+ messages/day to Gmail). Know which set applies before you tell the user
what is mandatory.

Two findings matter more than the rest:

- **`p=none` with no `rua`** is the most common state and is not a passing grade. It means
  nothing is enforced and nobody is reading the reports, so authentication failures are
  invisible.
- **Cold outbound from the primary domain** puts transactional and cold mail on one
  reputation. Recommend a dedicated sending subdomain or a separate domain.

If the domain fails authentication, stop and fix that. Rewriting the email is wasted work.

## Step 2 — Establish who may be emailed

Ask where the recipients are. This is not optional detail — it changes what is legal:

- **US (CAN-SPAM).** No prior consent needed. But the message must carry a valid physical
  postal address, a working opt-out, and non-deceptive headers and subject.
- **EU/UK (GDPR + ePrivacy).** Consent rules for unsolicited email vary by member state,
  and B2B is treated differently from B2C. The UK permits mail to corporate subscribers
  without consent; Germany effectively does not. GDPR also requires a lawful basis —
  usually legitimate interests — which must be assessed and documented before sending.
- **Canada (CASL).** Consent is required, express or implied. "Conspicuously published
  business address, message relevant to their role" is the implied-consent route most cold
  outbound relies on, and it has conditions.

Full requirements, including exactly what must appear in the message body per regime, are
in `references/compliance.md`. Read it before drafting for any non-US recipient.

State the constraint to the user; do not quietly drop it. And be clear that this is
operational guidance, not legal advice — a real list crossing several jurisdictions
warrants counsel.

## Step 3 — Find the trigger

An email needs a specific, checkable, recent reason it was sent to **this** person **now**.
No trigger means it is a broadcast wearing a costume, and it reads as one.

Usable triggers, roughly in descending order of strength: they are hiring for the problem
you solve; they shipped or announced something that creates the need; they raised; they
changed role; they published a specific technical or strategic position; a peer company
they benchmark against just did the thing.

Weak triggers, which are usually automation tells: "I loved your post," "I saw you're the
VP of X," "congrats on the funding" with nothing following it, and anything that a merge
field could have produced.

If there is no trigger, that is the finding. Say so before writing copy.

## Step 4 — Draft

Read `references/copy.md` first. It has the anatomy, the subject-line rules, the
anti-patterns with the reason each one fails, and worked before/after rewrites in
`assets/example-emails.md`.

The constraints that matter most:

- **50 to 80 words.** 125 is a ceiling, not a target. The ask must be visible on a phone
  without scrolling.
- **One sentence per section.** The second sentence is almost always you explaining the
  inference you just drew — cut it. Give them the observation, not your conclusion about it.
- **The first sentence is about them, and is falsifiable.** If it could be sent to anyone,
  it is not a first sentence.
- **The ask is concrete *and* soft.** Name one small thing you can send immediately, then
  close in two words: *"I can send the 20-line query we used. Want it?"* Soft-but-vague
  ("worth a look?") fails because the recipient has to invent the next step; concrete-but-
  heavy (a calendar link) fails because it asks for thirty minutes from a stranger.
- **One question mark.** Two questions halve the odds of either being answered.
- **One link maximum, no attachments.** Both are reputation and filtering liabilities in a
  first touch.

## Step 5 — Score the draft

```bash
python3 scripts/score_email.py draft.txt
```

It reports word count, the ask, question count, link count, the you/we ratio, reading
grade, jurisdiction-required elements, and phrase-level flags — quoting the offending text
rather than just naming a rule. `--jurisdiction us|eu|ca` adjusts the compliance checks.

Treat the score as a lint pass, not a verdict. A 100 does not make an email worth sending;
a trigger-less email can score perfectly. Fix what it flags, then judge the draft on
whether it earns a reply.

## Step 6 — Build the sequence

Two to three follow-ups, each carrying **new information** rather than "bumping this," and
a hard stop. Timing, thread strategy, stop rules, and the arithmetic of what volume a
mailbox can carry are in `references/sequences.md`.

## What to report back

When auditing an existing outbound program, structure the finding as:

1. **Delivery posture** — the domain audit table, with the one fix that matters most.
2. **Compliance gaps** — per jurisdiction, what is missing from the message.
3. **Copy** — the score, then the rewrite, then what specifically changed and why.
4. **What cannot be known** — if they are quoting open rates, say why those numbers are
   unreliable and what to instrument instead.
