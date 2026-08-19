# Report structure

The person who decides whether to fund the work is usually not the person who implements it.
So the report front-loads a summary that stands alone, and pushes methodology to an appendix
where it stays available for scrutiny without blocking the decision.

Use this structure:

```markdown
# SEO Audit — [property] — [window]

## Executive summary
Three to five sentences. What is the state of organic search for this site, what is the
single biggest opportunity, and what is the single biggest risk. Name the estimated click
upside of acting on the top three findings. No jargon — this paragraph gets forwarded.

## Scorecard

| Metric | Current 28d | Previous 28d | Same 28d last year |
|---|---|---|---|
| Clicks | | | |
| Impressions | | | |
| Avg. position (impression-weighted) | | | |
| CTR | | | |
| Pages with ≥1 click | | | |

## Priority findings

For each, in impact ÷ effort order — the top three get full treatment:

### N. [Finding, stated as the problem not the fix]
**Evidence:** the measured GSC numbers, with the window.
**Mechanism:** why this is happening, and how confident you are.
**Estimated impact:** the arithmetic, shown inline.
**Recommendation:** the specific action, on the specific URLs.
**Effort:** S / M / L, with what it involves.

## Opportunity table
Striking-distance and CTR findings, grouped by landing page, ranked by estimated
incremental clicks per month. One row per page, not per query.

## Technical findings
On-page and indexability issues, grouped by whether they affect a template or single
pages. Template-level issues first — they scale.

## What we are NOT recommending
Findings deliberately not acted on, and why: seasonal declines, queries lost to SERP
features, apparent cannibalization that is actually intended architecture. This section
prevents someone else re-raising them in three months as though they were missed.

## Appendix A — Property CTR curve
Median CTR by position, with row counts per bucket.

## Appendix B — Data caveats
- Property and type (domain vs URL-prefix), and what that scope excludes
- Date windows, and the freshness lag applied
- Anonymized-query gap: query-dimension clicks vs property total
- URL Inspection sample size and selection method
- Any analysis that could not be run, and what blocked it
```

## Writing notes

**State findings as problems, not fixes.** "Product pages have duplicate titles" invites the
reader to think; "Rewrite 40 titles" invites them to argue about the number.

**Show the arithmetic inline.** A number the reader cannot reconstruct is a number they
cannot trust, and the first one they doubt discredits the rest of the report.

**Group by work, not by row.** Fifteen queries on one page is one task. Reporting it as
fifteen findings misrepresents both the effort and the priority.

**Keep the "not recommending" section.** It is short, and it is often the part that
demonstrates the audit was actually thought about rather than generated.

**Separate measured from inferred throughout.** Measured numbers can be stated flatly.
Hypotheses need to be labeled as such, with the evidence for and against — including when
the honest answer is that the data cannot distinguish between two plausible causes.
