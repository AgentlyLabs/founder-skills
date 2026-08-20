# Compliance by jurisdiction

Operational guidance, not legal advice. A list spanning several jurisdictions, or any
program at scale, warrants review by counsel. What follows is the structure of each regime
and what it forces into the message body — the parts that change how you draft.

The governing question is always **where the recipient is**, not where the sender is.

## United States — CAN-SPAM

15 U.S.C. §7701 et seq., implemented at 16 C.F.R. Part 316.

**Consent: not required.** This is the fact that makes US cold outbound viable and that
people wrongly generalize to the rest of the world.

**Required in every commercial message:**

- Accurate `From:`, `Reply-To:`, and routing information. No false or misleading headers.
- A subject line that is not deceptive relative to the body.
- Identification that the message is an advertisement. This can be satisfied by context;
  it need not be a banner. Messages sent with the recipient's affirmative consent are
  exempt from this specific item.
- **A valid physical postal address** for the sender. A PO box or registered agent address
  qualifies. This is the requirement most cold email omits.
- **A working opt-out mechanism**, functional for at least 30 days after sending.

**Required after sending:** honor opt-outs within **10 business days**. Do not require a
login, a fee, or any information beyond an email address to opt out. Once someone opts
out, their address may not be sold or transferred except to a provider helping you comply.

**Liability is per message** and civil penalties are adjusted annually for inflation —
above $50,000 per individual email in recent years. Confirm the current figure against the
FTC's published adjustment rather than quoting a remembered number. Note that hiring a
vendor does not transfer liability; the party whose product is promoted remains on the hook.

There is no B2B exemption in CAN-SPAM. It applies to business addresses.

## EU and UK — GDPR plus ePrivacy

Two instruments stack, and the second is the one that governs whether you may send.

**GDPR (Regulation 2016/679)** requires a lawful basis for processing the personal data —
and a work email address that identifies a person is personal data. For B2B outreach the
basis is normally **legitimate interests**, Art. 6(1)(f), which is not self-declaring: it
requires a documented balancing test (a Legitimate Interests Assessment) weighing your
interest against the recipient's rights and reasonable expectations. Do it before sending,
and keep it.

GDPR also carries obligations independent of the send:

- **Transparency** — the recipient must be able to learn who you are, what data you hold,
  where you got it, and why. In practice this means a privacy notice link and an
  identifiable sender.
- **The right to object** (Art. 21) — absolute for direct marketing. On objection you must
  stop, which means a suppression list, not just a deleted row.
- **Source disclosure** (Art. 14) — where data was not collected from the person directly,
  you must tell them the source on request. Scraped lists make this hard to answer honestly.

**ePrivacy Directive (2002/58/EC), Art. 13** governs unsolicited direct marketing by
electronic mail. Art. 13(1) requires prior consent for email marketing to natural persons.
Art. 13(5) leaves it to each member state whether to extend that protection to legal
persons — which is why B2B cold email is **legal in some member states and not others**,
and why "is cold email legal in the EU" has no single answer.

Two illustrative poles:

- **UK (PECR, reg. 22).** Consent is required for individual subscribers. Corporate
  subscribers — limited companies, LLPs, public bodies — are outside that restriction, so
  B2B mail to a company address is permitted without prior consent, subject to the GDPR
  obligations above and to honoring objections. Sole traders and most partnerships count
  as individual subscribers, so a `@` at a one-person consultancy is not covered.
- **Germany (UWG §7).** Unsolicited commercial email is treated as an unreasonable
  nuisance without prior express consent, and this applies to business recipients too.
  Enforcement is largely private, via competitor and association actions, which makes it
  practically risky rather than theoretically risky.

France, Italy, Spain, and the Netherlands each sit at different points between those two.
When a user has EU recipients, ask which countries and check the specific national rule.
Do not answer "yes, with legitimate interests" as though it settled the question — that
answers GDPR while ignoring ePrivacy.

**In the message:** identify the sender and the commercial nature, provide a functioning
opt-out in every message, and link a privacy notice.

## Canada — CASL

S.C. 2010, c. 23. The strictest of the three, and the one most often overlooked.

**Consent is required** — either express or implied. Cold outbound depends on implied
consent, which has enumerated routes with conditions. The two that matter:

- **Conspicuously published business address.** The address was published without a
  statement that unsolicited commercial email is not welcome, and **your message relates to
  the recipient's business role or functions**. A generic pitch to a published address does
  not qualify; relevance to their role is a condition, not a nicety.
- **Existing business or non-business relationship** — a purchase or contract within the
  preceding **two years**, or an inquiry from them within the preceding **six months**.

Note the asymmetry with the US: a scraped address that was not conspicuously published, or
a message unrelated to the recipient's role, has no consent basis at all.

**Required in every message:**

- Sender identification, including on whose behalf the message is sent if different.
- Contact information — mailing address plus a phone number, email, or web address — that
  remains **valid for at least 60 days** after sending.
- An unsubscribe mechanism, honored within **10 business days**.

**Penalties** reach CAD $1 million for individuals and CAD $10 million for organizations
per violation, and CASL includes director and officer liability. It is enforced.

## Drafting consequences

What this means at the keyboard, regardless of regime:

- **Every message carries a physical address and a working opt-out.** Required in the US
  and Canada, and good practice in the EU. There is no jurisdiction where omitting them
  helps.
- **A plain-text opt-out line satisfies the requirement** and reads far better in a 1:1
  email than a marketing footer. "If you'd rather not hear from me, just say so and I'll
  close the file" is a functioning mechanism, provided you honor it.
- **Relevance to the recipient's role is a legal element in Canada**, not only a copy
  virtue. The trigger discipline in `copy.md` is doing double duty.
- **Suppression is permanent and cross-campaign.** An opt-out that only stops one sequence
  is a violation waiting for the next send.
- **The narrower the list, the easier every one of these gets.** Volume is what turns
  compliance from a paragraph into a program.
