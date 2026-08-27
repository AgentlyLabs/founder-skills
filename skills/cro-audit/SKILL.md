---
name: cro-audit
description: Run a rigorous conversion rate optimization audit on a real landing page, signup flow, or checkout — measuring the page in a browser and against analytics data rather than scoring it against a generic checklist — then produce prioritized fixes with lift ranges, and an experiment plan with the sample size and duration each test actually requires. Use this whenever the user wants a CRO audit, landing page teardown, or conversion review; asks why their traffic is not converting, why signups or demo bookings are flat, or why people abandon a form, signup, checkout, or onboarding flow; asks whether a headline, CTA, pricing page, or form is any good; asks how to improve conversion rate, reduce bounce, or increase signups; asks to design, size, or interpret an A/B test, or whether a test result is real. Trigger even when the user never says "CRO" or "conversion" — "roast my landing page", "we get 4,000 visitors a month and 11 signups", "is this test result significant", and "which of these two headlines should I ship" are all this skill.
---

# CRO Audit

## Why this skill exists

Two things pass for conversion optimization, and both are worthless.

The first is the checklist. Thirteen principles, twenty-seven tips, "add urgency and
social proof" — advice that could be written without ever loading the page. It is
unfalsifiable, it applies equally to every site, and it produces a document the founder
skims once and never opens again.

The second is the fake win. A test runs for four days, 380 visitors, 4.1% against 3.2%,
someone declares a 28% lift and ships it. The confidence interval on that difference runs
from −38% to +140%. The number was noise. The team now believes a false thing about their
customers and will make the next three decisions from it.

This skill exists to avoid both. Two disciplines do all the work:

1. **Every finding cites a measurement taken from this page or this account.** Not a
   principle, not a heuristic — a number, with a key, recorded in `measurements.json`. A
   claim you cannot attach a measurement to is an opinion, and opinions go in a clearly
   labeled section at the end or nowhere at all.
2. **No lift is asserted without its arithmetic, and no test is proposed without its
   sample size.** If the required sample takes eleven months to accumulate at this site's
   traffic, the honest recommendation is not to run the test. Saying so is the most
   valuable output this skill produces, and almost nobody says it.

The uncomfortable consequence, stated up front so it does not come as a surprise in the
report: **most sites cannot A/B test.** Below roughly 1,000 conversions per month you
cannot detect the effect sizes real changes produce, and pretending otherwise burns
months. For those sites the job is different — ship changes on evidence and judgment,
measure the funnel over long windows, and get your resolution from qualitative sources
instead. `references/experiment-design.md` gives the threshold arithmetic.

## Step 0 — Scope

Establish these before measuring anything. Ask only what you cannot infer.

- **The URL, and the traffic source it is built for.** A page has no context-free
  quality. A landing page for one ad group is judged against that ad's promise; a
  homepage serving eight intents is judged differently and most page-level CRO checks do
  not apply to it. If there is a paid source, get the actual ad copy or the query — the
  message-match check is worthless without it.
- **The conversion action**, named exactly. "Signup" is ambiguous: account created,
  email submitted, activated, paid? Everything downstream depends on the denominator and
  numerator being stated once, plainly.
- **The current numbers**, if any: visitors and conversions per week, and the value of a
  conversion. Without volume you cannot size an experiment; without value you cannot
  rank findings. If the user does not know, the first finding is that.
- **What already got tried.** Failed tests are data, and re-proposing a change that lost
  last quarter destroys trust in the whole report.

If the user has analytics (GA4, PostHog, Amplitude, Plausible, a data warehouse), check
for an MCP connection with `ToolSearch` before assuming you only have the page. Funnel
data changes the audit from "here is what looks wrong" to "here is where the money
leaks", which is a different and much better document.

## Step 1 — Measure the page

Two layers, because they answer different questions.

**Static and network layer** — deterministic, run the script:

```bash
python3 scripts/measure.py https://example.com/landing --source-copy "Ad headline here" --assets -o measurements.json
```

It fetches the page and records form field inventory and input types, attention ratio,
heading text, CTA labels, price and trust-signal presence, viewport and mobile
configuration, transfer weight, render-blocking resources, and a message-match score
against `--source-copy`. Every value lands in `measurements.json` under a stable key.
Those keys are what findings cite.

**Rendered layer** — what only a real browser knows. Use the browser tools:

1. `mcp__Claude_Browser__preview_start` with the URL, then
   `mcp__Claude_Browser__resize_window` to `mobile` (375×812) and to 1366×768 — the two
   viewports that matter, and neither is your laptop.
2. `mcp__Claude_Browser__computer` with `action: "screenshot"` at each. Look at it.
   Several of the highest-value findings in a CRO audit are only visible to a pair of
   eyes: the CTA that sits below a cookie banner, the hero image that eats the fold, the
   headline that is technically present and completely unreadable.
3. `mcp__Claude_Browser__javascript_tool` for the measurements the DOM can answer —
   `references/page-checks.md` carries the exact snippets for fold position of the
   primary CTA, tap target sizes, contrast on the CTA, and horizontal overflow.

Merge the rendered values into `measurements.json` under the same key convention. If you
cannot measure something, record it as `null` with a reason rather than dropping it —
an unmeasured check is a known gap, and known gaps belong in the report.

Field performance data (LCP, INP, CLS from real users) comes from the CrUX API, not from
a lab run. Lab numbers on your fast laptop are not what your visitors experience, and
speed findings built on them are routinely wrong by a factor of three.

## Step 2 — Run the checks

`references/page-checks.md` is the workhorse. It lists every check in three tiers, with
its threshold, the reasoning behind the threshold, how to measure it, and what the fix
is. Work the tiers in order and stop taking tier 3 seriously.

Before writing a single finding, read `references/evidence-base.md`. It separates what
has replicated evidence behind it from what is confidently repeated folklore. Button
color, exit-intent popups, and "above the fold" as a universal law are in the folklore
section, and reporting them as findings is how a CRO audit gets dismissed by anyone
technical.

## Step 3 — Diagnose the funnel, if you have data

A page audit finds what is wrong on one screen. A funnel diagnosis finds which screen is
worth fixing, which is a strictly better question. `references/funnel-diagnosis.md`
covers step-loss ranking by absolute users rather than percentage, segment splits with
minimum-volume gates, form field abandonment, and the measurement-validation pass that
has to come first — if the events are miscounted, every number downstream is fiction.

```bash
python3 scripts/ab.py funnel --steps steps.json
```

Rank by **absolute users lost × value per user**, never by the biggest percentage drop.
The largest percentage drop is usually at a low-volume step and fixing it moves nothing.

## Step 4 — Estimate lift honestly

For each finding, state the expected effect as a **range**, with the arithmetic visible
and the mechanism named:

> **Form asks for 11 fields; 6 are not required to deliver the trial.**
> `[m: form.field_count = 11, form.required_count = 9, form.unjustified = 6]`
> Field-count reductions of this size have produced completion gains in the 10–40%
> relative range across published tests, with wide variance by audience. At the current
> 3.1% page conversion, that is **3.4%–4.3%**, or **+9 to +37 signups/month** at 3,100
> monthly visitors. Mechanism: each additional field is a separate opportunity to
> reconsider, and phone number specifically signals a sales call the visitor did not
> agree to.

Three rules keep these from becoming fiction. Give a range, never a point estimate.
Name the mechanism, because a lift with no mechanism is a coincidence you are planning
around. And when the estimate rests on an external effect size rather than this site's
own data, say which — `references/evidence-base.md` marks what is safe to lean on.

## Step 5 — Write the experiment plan

This is where most audits quietly stop being useful, and where this one earns its keep.

For each proposed change, compute what testing it would actually cost:

```bash
python3 scripts/ab.py size --baseline 0.031 --mde-rel 0.15 --weekly-traffic 3100
```

The output gives sample size per arm, total, and weeks to conclusion at the site's real
traffic. Then sort every proposal into three buckets:

- **Testable** — reaches significance inside 4 weeks. Design the test properly:
  pre-registered metric, fixed horizon or a sequential method, full weekly cycles, an
  SRM check before anyone looks at the result.
- **Ship it** — the change is strictly better on reasoning and could never be tested
  here in a sane timeframe. Fixing a broken mobile input type does not need an
  experiment; it needs a deploy. Say so and move on.
- **Not a test, a decision** — the change is a real bet, the traffic will not resolve it,
  and it needs a different evidence source: five user tests, session recordings, support
  ticket clustering, or a customer call.

`references/experiment-design.md` covers sizing, why peeking invalidates fixed-horizon
p-values, novelty effects, sample ratio mismatch, and the multiple-comparisons trap in
post-hoc segment analysis.

If the user brings you an existing result to interpret, run it and report the interval:

```bash
python3 scripts/ab.py test --a 380/12000 --b 410/11940
```

Report the confidence interval before the point estimate, always. "A 7.8% relative lift,
95% CI −4.1% to +21.3%" is an honest sentence. "A 7.8% lift" from the same data is not.

## Step 6 — Write the report

Use `references/report-template.md`. It leads with the three highest-value findings and
the honest testing verdict, and pushes methodology to an appendix — the person deciding
whether to fund the work is rarely the person implementing it.

Then verify it:

```bash
python3 scripts/verify.py report.md measurements.json
```

Every finding must cite at least one measurement key, and every cited key must exist
with the stated value. This is the mechanical enforcement of discipline 1 — it is the
difference between an audit and a blog post. Fix every finding until it exits 0, then
paste the output for the user.

## Output layout

```
cro-audit/
  measurements.json     <- every measured fact, keyed. The receipt.
  report.md             <- findings, ranked by value, each citing keys
  experiments.md        <- the test plan with sizes, durations, and the ship/test/decide split
```

## Honesty rules

An audit's only product is trust in its conclusions. These outrank every individual
check.

- **Never report a finding you did not measure.** If a check could not run, list it as a
  gap. An unmeasured check is not a passed check.
- **Never assert a lift as a point estimate.** Ranges, with the arithmetic shown.
- **Never call a test without n, a confidence interval, and an SRM check.** A result that
  fails SRM is discarded, not interpreted — it means the assignment was broken.
- **Label the evidence class of every claim**: measured on this page, measured in this
  account, established externally, or hypothesis. Four different levels of trust.
- **Say when a test is not available.** Sites without the traffic deserve a real answer,
  not a test design that will never conclude.
- **Do not pad.** Eleven findings that matter beat forty that include button color. The
  tier 3 list in `references/evidence-base.md` exists to be left out of the report.
- **Attention ratio does not apply to homepages.** Several standard checks are specific
  to dedicated landing pages. Applying them to a homepage or docs page produces confident
  nonsense; each check in `page-checks.md` states its scope.

## Reference files

- `references/evidence-base.md` — what holds up, what is contingent, what is folklore.
  Read before writing findings.
- `references/page-checks.md` — every check, with thresholds, reasoning, and the exact
  measurement method. The workhorse.
- `references/funnel-diagnosis.md` — analytics-side analysis and the validation pass.
- `references/experiment-design.md` — sizing, stopping rules, and the failure modes.
- `references/report-template.md` — output structure.
- `scripts/measure.py` — page measurement to `measurements.json`.
- `scripts/ab.py` — sample size, significance, funnel math. `--help` for the full set.
- `scripts/verify.py` — enforces that every finding cites a real measurement.
