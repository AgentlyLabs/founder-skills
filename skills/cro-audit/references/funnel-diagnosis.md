# Funnel diagnosis

A page audit tells you what is wrong on one screen. A funnel diagnosis tells you which
screen is worth fixing. Always prefer the second question when the data exists.

## Step 0 — Validate the measurement before believing any of it

Skip this and every number downstream is fiction. It takes ten minutes and it fails more
often than people expect.

- **Reconcile the bottom of the funnel against the source of truth.** Analytics
  conversions for last month versus rows in the database, or Stripe charges. A gap under
  ~5% is normal (ad blockers, consent rejection, tracking-prevention). A gap of 30% means
  the analytics number is not measuring what its name says, and the audit reports that
  before anything else.
- **Check for double-firing.** Conversions exceeding backend records, or a step with
  greater than 100% step conversion, means an event fires on render and on route change,
  or the thank-you page is reachable directly and gets bookmarked.
- **Exclude internal and bot traffic.** Office IPs, staging referrals, uptime monitors,
  and headless traffic inflate the denominator and depress the rate. A "conversion
  problem" that is really a bot problem is a real audit finding.
- **State consent-banner effects.** If analytics only fires post-consent, the denominator
  is consenting users, not visitors, and rates are systematically overstated.

## Step 1 — Define the rate once, in writing

Most disagreements about "our conversion rate" are two people using different
denominators. Write it down in the report's first paragraph:

> Conversion rate = *unique users* who completed *checkout_success* ÷ unique users who
> viewed */pricing*, same session, 28-day window, bots excluded.

Sessions and users give different numbers, and neither is wrong — undeclared is wrong.
For funnels spanning days, a session-scoped funnel undercounts badly; use user-scoped
with an explicit attribution window.

## Step 2 — Rank steps by absolute loss, never by percentage

```bash
python3 scripts/ab.py funnel --steps steps.json
```

`steps.json` is an ordered list:

```json
[
  {"name": "landing_view",    "users": 12480},
  {"name": "signup_start",    "users": 3110},
  {"name": "signup_submit",   "users": 1240},
  {"name": "email_verified",  "users": 1050},
  {"name": "activated",       "users": 312}
]
```

The script reports step conversion, absolute users lost, cumulative conversion, and loss
ranked by **users lost × value per user** when `--value` is supplied.

**Why absolute, not percentage:** the largest percentage drop is very often at a
low-volume step near the bottom, where fixing it moves a handful of users. The step that
loses 9,370 people is the one worth a week of work even if its percentage looks
unremarkable. Reports that rank by percentage consistently send teams to optimize the
wrong screen.

**Expect the top-of-funnel step to dominate**, and resist the urge to treat that as
uninteresting. Landing → signup_start is where most of the loss is on most sites, and it
is where the page checks in `page-checks.md` apply.

## Step 3 — Segment, with a volume gate

Split the funnel by, in rough order of yield:

1. **Device.** Mobile versus desktop conversion gaps of 2–3× are common and usually
   reflect a genuinely broken mobile experience rather than differing intent. Cross-check
   against `mobile.*` findings — those two sections should corroborate each other.
2. **Traffic source.** Paid, organic, direct, referral. A bad blended rate is frequently
   one bad source averaged into three fine ones. Also the fastest way to find a message
   match problem: a single ad group converting at a third of its siblings.
3. **New versus returning.**
4. **Geography and language**, if there is meaningful international traffic.
5. **Landing page**, if traffic distributes across many entry points.

**Volume gate:** do not report a segment with fewer than ~100 conversions in the window,
and never report a segment rate computed on single-digit conversions. Use
`ab.py test --a x/n --b y/m` to check whether a segment difference is distinguishable from
noise before writing it as a finding — many are not.

**These are descriptive splits, not experiments.** A segment difference is a hypothesis
about a cause. Say so in the report rather than implying the segment caused the gap.

## Step 4 — Form-level analysis

Where a form is the bottleneck, the field is the unit of analysis.

- **Field abandonment** — which field is focused last before the visitor leaves. This is
  the single most useful funnel measurement available and most tools support it. The
  answer is usually phone number, company size, or an address block.
- **Time in field** — a field taking a long time is either confusing or asking for
  something the visitor has to go look up. Both are findings.
- **Validation error rate per field** — a field with a 40% error rate has a format the
  visitor cannot guess, or validation that is wrong. Check whether the error message says
  what to do or merely that something is invalid.
- **Retry rate on submit** — repeated submits mean errors are appearing somewhere the
  visitor cannot see, often above the viewport after a scroll.

If field-level data is unavailable, say so as a gap, and get the equivalent from ten
session recordings filtered to sessions that reached the form and did not submit.

## Step 5 — Connect the funnel to the page

The output of this section is not a list of drop-offs. It is a **decision about where the
page audit's findings get applied**, and it belongs at the top of the report:

> 75% of total loss occurs at landing → signup_start, concentrated on mobile (mobile
> converts at 1.1% vs desktop 4.3% on the same page). The tier 1 mobile findings below
> are therefore the highest-value work available, ahead of every copy change.

That paragraph is what makes the audit actionable, and it is only writable when funnel
and page evidence are read together.
