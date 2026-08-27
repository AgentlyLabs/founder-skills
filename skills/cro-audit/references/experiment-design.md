# Experiment design

The section of the audit that decides whether the rest of it is real.

## The first question is not "what should we test"

It is **"can this site test anything at all."** Answer it before proposing a single
experiment, because the answer is usually no and everyone involved is better off knowing.

Sample size per arm, two-sided, α = 0.05, power = 0.80:

```
n = (z(1−α/2) + z(power))² × (p₁(1−p₁) + p₂(1−p₂)) / (p₂ − p₁)²
```

Visitors **per arm** needed to detect a given *relative* lift:

| Baseline CR | +5% rel | +10% rel | +20% rel | +50% rel |
|---|---|---|---|---|
| 1% | 637,000 | 163,100 | 42,700 | 7,700 |
| 2% | 315,200 | 80,700 | 21,100 | 3,800 |
| 3% | 207,900 | 53,200 | 13,900 | 2,500 |
| 5% | 122,100 | 31,200 | 8,200 | 1,500 |
| 10% | 57,800 | 14,700 | 3,800 | 700 |

Reproduce any cell with `python3 scripts/ab.py size --baseline 0.03 --mde-rel 0.20`.

Read the 3% row, because it is roughly where B2B landing pages live. Detecting a 20%
relative improvement needs 13,900 visitors **per arm** — 27,800 total. At 2,000 visitors
a week that is **14 weeks**. At 500 a week it is over a year.

Two consequences the report must state plainly:

- **A site under ~1,000 conversions/month cannot run a normal A/B program.** Not "should
  be careful" — cannot. Every test will either run for a quarter or conclude nothing.
- **The only detectable effects at low volume are enormous ones.** Which means if a test
  at that scale does report a winner, the most likely explanations are that you peeked,
  that assignment was broken, or that you got a false positive — not that you found a 50%
  lift.

## Set the MDE from business value, not from what you can detect

The minimum detectable effect is the smallest improvement that would be **worth
shipping**, decided before you compute anything. Working backwards — "we can detect 20%,
so let's call the MDE 20%" — is how teams end up running tests whose only possible
outcomes are "inconclusive" and "false positive."

If the smallest worthwhile lift is 5% and you cannot detect 5%, the test is not
available. That is a finding, not a reason to relabel the MDE.

## The three buckets

Sort every proposed change. This is the deliverable in `experiments.md`.

**Ship it.** Correct on reasoning, no experiment needed. Defects: broken input types,
missing autocomplete, a CTA occluded by a cookie banner, an unstated card requirement, a
form field the backend does not store. Spending a 14-week test slot on a defect is the
most expensive mistake in this whole document.

**Test it.** Reaches significance inside four weeks at real traffic. These get a full
design: one pre-registered primary metric, fixed sample size computed in advance, whole
weekly cycles, an SRM check, and a written prediction before launch.

**Decide it.** A genuine bet — new positioning, a different pricing model, a restructured
flow — that this site's traffic will never resolve. The answer is a different evidence
source, not a longer test: five moderated user tests, twenty session recordings watched
end to end, a support-ticket cluster, or ten sales calls. Say which, and say what
question it answers. A team that spends four weeks on qualitative evidence learns more
than one that spends four months on an underpowered experiment.

## Stopping rules, and why peeking breaks everything

A fixed-horizon p-value is only valid at the sample size you committed to in advance.
Checking daily and stopping when it crosses 0.05 does not "get the answer sooner" — it
changes what the answer means.

Simulated A/A tests (no real difference at all), stopping the first time p < 0.05:

| Looks at the data | False positive rate |
|---|---|
| 1 (at the planned n) | 4.9% |
| 5 | 13.3% |
| 10 | 17.0% |
| 20 | 23.7% |
| 40 | 28.1% |

Reproduce with `python3 scripts/ab.py peek-sim --looks 20`.

A team checking the dashboard every morning for a three-week test is at roughly one in
four odds of "winning" a test where nothing is happening. This single mechanism explains
most of the CRO case studies in circulation.

Two valid options:

1. **Fixed horizon.** Compute n in advance, do not look at significance until you reach
   it. Monitoring for *breakage* — error rates, SRM — is fine and encouraged; monitoring
   the primary metric is not.
2. **A sequential method.** Always-valid p-values, alpha spending, or a Bayesian approach
   with a pre-committed decision rule. These are built to be looked at continuously. If
   the user's testing tool advertises "peek any time", it should be using one of these —
   check, because several tools claim it while computing fixed-horizon p-values.

Whichever you choose, **run whole weekly cycles.** Tuesday traffic does not behave like
Saturday traffic, and a test that ends mid-week has a composition difference baked into
it. Minimum one full week even when n is reached on day three; two is better because of
novelty.

## Before interpreting any result

**Sample ratio mismatch first.** If you assigned 50/50 and observed 12,000 / 11,940, run
the check. A significant SRM means assignment or logging is broken, and the result must
be **discarded, not interpreted** — including a result you like. Broken assignment is
usually correlated with something (a bot filter, a redirect that drops one arm, a race in
the SDK), so the winner is an artifact.

```bash
python3 scripts/ab.py test --a 380/12000 --b 410/11940
```

The command reports SRM before it reports the lift, deliberately.

**Then the interval, before the point estimate.** Report "+7.8% relative, 95% CI −4.1% to
+21.3%" — a sentence that correctly conveys "we learned very little." The same data
written as "+7.8% lift" is a false statement about the world.

**Novelty and primacy.** Returning users react to change as change. A shiny new banner can
lift for ten days and revert. If the audience is mostly returning users, either run long
enough for the effect to settle or segment to new users only — decided in advance.

**Post-hoc segments are a trap.** Slicing a null result by device, country, browser, and
source until something reaches p < 0.05 is guaranteed to find something. Twenty segments
at α = 0.05 yields roughly a 64% chance of at least one false positive. Pre-register the
segments you will look at, or treat segment findings as hypotheses for a new test and
label them that way.

**Simpson's paradox on splits.** A variant can lose on mobile, lose on desktop, and win
overall if the traffic mix shifted between arms. If the aggregate and the segments
disagree, the mix changed — go back to the SRM check.

## Interpreting a result someone brings you

Almost always, someone arrives with "we got a 34% lift." Run the numbers before
responding, and expect one of four outcomes:

1. **Real and precise** — a tight interval well away from zero. Rare, and usually a
   defect fix rather than a persuasion change.
2. **Real but imprecise** — interval excludes zero but spans 2% to 60%. The direction is
   probably right; the magnitude is unknown. Do not put the point estimate in a board
   deck.
3. **Nothing** — interval spans zero. The correct summary is "we could not detect a
   difference", not "it didn't work" and certainly not "it works."
4. **Broken** — SRM fails, the test ran four days, or the metric changed mid-flight.
   No conclusion is available. Say so.

The fourth is the most common, and saying it plainly is the most useful thing this skill
does.

## What to do at low traffic instead

For the majority of sites that cannot run experiments, this is the real recommendation
section, and it should be written with the same seriousness as a test plan.

- **Fix the tier 1 defects and ship them together.** You will not attribute the gain
  precisely. That is an acceptable price, and pretending otherwise costs a year.
- **Measure at the funnel level over long windows** — month over month, with the
  denominator definition written down once so nobody re-derives it differently later.
- **Buy resolution qualitatively.** Five user tests on the actual signup flow surfaces
  more actionable failure than any test this site could power. Session recordings filtered
  to sessions that reached the form and did not submit are the single highest-yield hour
  available.
- **Increase the conversion rate's own resolution** by moving the measured event earlier
  in the funnel where volume is higher — form starts rather than completed purchases —
  while being explicit that it is a proxy metric.
