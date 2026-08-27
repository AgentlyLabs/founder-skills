# Report structure

Two files. `report.md` is read by whoever decides. `experiments.md` is read by whoever
implements. Keep them separate — merging them produces a document neither person finishes.

`scripts/verify.py` enforces the citation rule, so write findings in the format below
from the start rather than retrofitting keys at the end.

---

## report.md

### 1. What was measured

Four lines, no preamble. URL, traffic source, conversion action with its exact
denominator, and the window and volume behind any rates quoted.

> `https://example.com/trial` · paid traffic, ad group "invoice reconciliation" ·
> conversion = `signup_submit` ÷ unique users landing on this URL, 28 days ·
> 3,104 users, 96 conversions, 3.1%.

### 2. The verdict on testing

Second, deliberately — before any finding, because it governs how everything below should
be read.

> At 3.1% and 3,100 monthly visitors, detecting a 20% relative improvement requires 13,900
> visitors per arm — **9 months**. This site cannot run A/B tests on page-level changes.
> Every recommendation below is therefore either a defect to ship, or a bet to decide with
> qualitative evidence. Two items are marked testable; the rest are not.

### 3. The three things worth doing

Only three. Each with the measurement, the estimated range with its arithmetic, and the
effort. Everything else goes in section 5 and most readers will never get there — that is
the intended behavior.

> **1. The mobile form cannot be autofilled and shows the wrong keyboard.**
> `[m: mobile.input_type_errors = 4, mobile.autocomplete_missing = 7]`
> Seven of eight fields have no `autocomplete` token; the email field is `type="text"`.
> 71% of this page's traffic is mobile, converting at 1.1% against desktop's 4.3%.
> **Ship, do not test** — these are defects. Effort: S, one afternoon.
> Estimated: no defensible point estimate; the mobile/desktop gap bounds the opportunity
> at up to +90 signups/month if mobile reached desktop's rate, which it will not fully.

Note what that example does: cites keys, states evidence class, gives a bounded estimate
rather than an invented one, and refuses to fabricate precision.

### 4. Where the loss actually is

The funnel paragraph from `funnel-diagnosis.md` step 5, with the step table. Omit this
section entirely if there is no analytics access — do not substitute guesses.

### 5. Full findings

Grouped by tier, each with key citations. Tier 1 items are defects; tier 2 items carry a
proposed test or an explicit "decide, do not test." Tier 3 does not appear.

Format per finding, one paragraph:

```
**<What is wrong, stated as a fact>**
`[m: key = value, key = value]`
<Mechanism — why this costs conversions.>
<Estimate as a range with arithmetic, or an explicit statement that none is defensible.>
<Ship / Test / Decide. Effort: S|M|L.>
```

### 6. What could not be measured

Every declared gap from `page-checks.md`. This section is what separates an audit from a
guess, and reviewers read it first to decide whether to trust the rest.

### 7. Appendix — method and caveats

Measurement date, tooling, viewport sizes, whether speed data is field or lab, the
analytics denominator definition, and the evidence class of every external effect size
leaned on. Anything that would let someone reproduce or dispute a number.

---

## experiments.md

### Bucket A — ship now, no test

Table: change · files or surfaces touched · why no test is needed · effort.

### Bucket B — testable

One block per test:

- **Hypothesis**, written as a prediction with a direction and a mechanism. "Removing the
  phone field will increase form completion, because it currently signals a sales call" —
  not "we think this will improve things."
- **Primary metric**, one, pre-registered. Guardrail metrics listed separately.
- **MDE**, set from business value, with the reasoning.
- **Sample size and duration**, from `ab.py size`, with the command shown.
- **Stopping rule**: fixed horizon at n, or the named sequential method. State explicitly
  that the primary metric will not be checked before n.
- **Pre-registered segments**, if any.
- **Kill criteria**: what breakage aborts the test early.

### Bucket C — decide, do not test

Change · why the traffic cannot resolve it · the evidence source that can · what question
it answers · roughly what it costs to get.

### Appendix — the sizing table for this site

`ab.py size` output across a few MDEs at this site's actual baseline and traffic. It is
the artifact the team will reuse every time someone proposes a test, and having it in
writing prevents the next six months of underpowered experiments.
