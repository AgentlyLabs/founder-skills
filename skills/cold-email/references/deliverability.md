# Deliverability: what mailbox providers actually require

Read this to interpret `scripts/check_domain.py` output. Everything here is a published
provider requirement or an RFC, not inference from results.

## The three authentication mechanisms

**SPF** (RFC 7208) — a DNS TXT record listing which servers may send for the domain.
Published at the domain root as `v=spf1 ... all`. It authenticates the SMTP envelope
sender (`MAIL FROM`), *not* the `From:` header the recipient sees, which is why SPF alone
does not prevent spoofing of the visible address.

Two hard limits people trip over:

- **10 DNS lookup maximum.** Each `include:`, `a`, `mx`, `ptr`, `exists:`, and `redirect=`
  costs at least one lookup, and nested includes count recursively. Exceeding it produces
  `permerror`, which most receivers treat as a failure. Adding one more SaaS sender to an
  already-long record is a classic way to break a working setup.
- **One SPF record per domain.** Two `v=spf1` TXT records is a `permerror`, not a merge.

The qualifier at the end is a policy statement: `-all` (hard fail), `~all` (soft fail),
`?all` (neutral), `+all` (pass anything — effectively no policy, and a serious finding).

**DKIM** (RFC 6376) — a cryptographic signature over selected headers and the body,
verified against a public key at `<selector>._domainkey.<domain>`. Because the signature
travels with the message, DKIM survives forwarding in a way SPF does not. The selector name
is chosen by the sending platform, which is why it must be probed rather than derived —
Google Workspace uses `google`, Microsoft `selector1`/`selector2`, and ESPs vary.

Use a 2048-bit key. 1024-bit is still accepted but is the weaker option and some receivers
discount it.

**DMARC** (RFC 7489) — a policy record at `_dmarc.<domain>` telling receivers what to do
when authentication fails, plus a reporting address. Requires **alignment**: the domain
that passed SPF or DKIM must match the `From:` header domain. This is the piece that makes
the other two meaningful.

- `p=none` — monitor only. Nothing is enforced.
- `p=quarantine` — failures go to spam.
- `p=reject` — failures are rejected outright.
- `adkim`/`aspf` — `r` (relaxed, organizational-domain match, the default) or `s` (strict,
  exact match).
- `rua=mailto:...` — where aggregate reports go. **A policy with no `rua` means nobody is
  reading the failure data**, which is the entire diagnostic value of DMARC.

`p=none` with no `rua` is the most common configuration in the wild and is functionally
equivalent to having no DMARC at all.

## Provider requirements, and the distinction almost everyone gets wrong

**Google (Gmail), effective February 2024:**

- *All senders* — must have SPF **or** DKIM, valid forward and reverse DNS (PTR) on sending
  IPs, and messages formatted per RFC 5322. Must not spoof Gmail `From:` headers.
- *Bulk senders*, meaning **5,000 or more messages per day to Gmail addresses** — must have
  SPF **and** DKIM **and** a DMARC policy on the From domain, with at least one of SPF or
  DKIM aligned to it; must keep the Postmaster Tools spam rate **below 0.30%**; and must
  offer one-click unsubscribe on commercial mail.

**Yahoo** published matching requirements on the same timeline.

**Microsoft** announced equivalent requirements for high-volume senders (5,000+ per day) to
consumer Outlook/Hotmail domains, effective May 2025: SPF, DKIM, and DMARC.

The practical consequence for cold outbound: a genuinely targeted program sends far fewer
than 5,000/day to any one provider, so the *bulk* rules are not binding — but the
all-senders authentication rule is, and it is enforced. Do not tell a user that DMARC is
legally mandatory for them if they send 40 emails a day. Tell them it is how they find out
their mail is failing.

**One-click unsubscribe** (RFC 8058) requires both headers, not just the first:

```
List-Unsubscribe: <https://example.com/u/abc123>, <mailto:unsub@example.com>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

Bulk senders must process these within two days. Note that a `List-Unsubscribe` header
alone, without `List-Unsubscribe-Post`, does not satisfy the one-click requirement.

## The spam rate threshold

Google's 0.30% figure is a rate over messages *delivered to Gmail*, visible only in
Postmaster Tools, and it is a ceiling rather than a target. Sustained rates above ~0.10%
already correlate with degraded placement. At cold-outbound volumes the arithmetic is
unforgiving: 3 complaints on 1,000 sends is 0.30%.

Register the sending domain in Google Postmaster Tools before starting. Without it, spam
rate is unobservable and the first symptom will be silence.

## Infrastructure decisions

**Use a dedicated sending domain or subdomain.** Reputation attaches to domains. Cold
outbound from the domain that also sends password resets and invoices puts those at risk,
and the damage is asymmetric — recovering a burned reputation takes far longer than losing
it. `outbound.example.com` or a separate `example-mail.com` isolates it.

**Warm up before volume.** A domain and IP with no sending history that suddenly emits
hundreds of messages looks exactly like a compromised account. Ramp over 3–4 weeks,
starting in the low tens per mailbox per day.

**Verify addresses before sending.** Bounce rate is a direct reputation input. A list with
5%+ invalid addresses damages the domain independently of anything in the copy.

**Custom tracking domain, or none.** Click-tracking links rewrite the URL to the tracking
provider's domain. Shared tracking domains are used by every other customer of that
provider, including the bad ones, and get blocklisted. If tracking is used, use a custom
CNAME'd subdomain.

**Provider send limits are a ceiling, not a plan.** Google Workspace caps external
recipients per day in the low thousands depending on plan, but reputation-safe cold volume
is an order of magnitude below that. Verify current limits against provider documentation
rather than quoting a remembered number.

## Metrics that lie

**Open rate is not measurable.** Apple's Mail Privacy Protection, introduced in iOS 15,
routes images through a proxy that preloads them regardless of whether the recipient read
anything, and it is enabled by default. Gmail has proxied images since 2013. An open rate
is now a blend of real opens, bot preloads, and security-scanner fetches, in unknown
proportions that vary with the recipient mix. It cannot support a conclusion.

Consequences to state plainly when a user quotes open rates:

- "50% open rate but no replies" is not a copy diagnosis. The 50% is not a real number.
- A/B tests on subject lines measured by open rate are measuring noise.
- Deliverability cannot be inferred from opens.

**What to instrument instead:**

- **Reply rate** — the only unambiguous positive signal, and the actual objective.
- **Bounce rate**, split hard vs. soft — a reputation input and a list-quality measure.
- **Spam complaint rate** from Postmaster Tools — the number providers act on.
- **Inbox placement**, via seed-list testing across providers, which is the closest
  available proxy for whether mail is landing at all.

One caveat on reply rate: automated out-of-office and bounce-notification replies inflate
it. Filter them before reporting.
