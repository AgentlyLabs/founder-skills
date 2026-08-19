# Analysis modules

Eight modules. Each states its inputs, threshold, ranking formula, and — most importantly —
the reasoning behind the cutoff, so you can adapt it to a site whose scale makes the default
wrong. Treat the numbers as calibrated defaults, not constants.

`scripts/analyze_gsc.py` implements modules 1–4 deterministically. Modules 5–8 need
judgment or extra data sources.

## Contents

1. [The property CTR curve (build this first)](#1-the-property-ctr-curve)
2. [Striking distance](#2-striking-distance)
3. [CTR underperformance](#3-ctr-underperformance)
4. [Keyword cannibalization](#4-keyword-cannibalization)
5. [Traffic decay with seasonality control](#5-traffic-decay-with-seasonality-control)
6. [Index coverage](#6-index-coverage)
7. [Device divergence](#7-device-divergence)
8. [Intent drift and zero-click pages](#8-intent-drift-and-zero-click-pages)

## 1. The property CTR curve

**Everything downstream depends on this, so build it first.**

From pull A (`page` + `query`, 28 days), bucket every row by rounded integer position 1–20,
and take the **median** CTR within each bucket. Median rather than mean, because a handful of
brand queries with 60% CTR will drag a mean upward and make the whole site look like it is
underperforming.

Only use buckets with at least 30 rows. Below that the median is noise; fall back to the
nearest populated bucket and note the interpolation.

Why the site's own curve rather than published benchmarks: real CTR at a given position
varies by a factor of five or more depending on SERP layout, how many ads and features sit
above the organic block, brand recognition, and query intent. Importing a generic
"position 1 = 31.7%" table into a site whose SERPs are dominated by AI Overviews and
shopping units produces impact estimates that are wrong by an order of magnitude. A site
compared against itself is defensible; the gap is real even if the absolute level differs
from someone else's benchmark.

Report the curve in the appendix. It is the most reusable artifact the audit produces.

## 2. Striking distance

Queries already ranking well enough that a modest improvement converts to real clicks —
usually the highest-ROI section of any audit.

**Inclusion:** average position between 8 and 20, and impressions ≥ the property's median
impressions-per-query over the window (or ≥100 in 28 days, whichever is higher).

Position 8–20 rather than the common "11–20": positions 8–10 are frequently below the fold
or below an AI Overview, so they behave much more like page two than their number suggests.
The upper bound at 20 reflects that moving from 25th to 5th is a content project, not an
optimization.

**Rank by estimated incremental clicks:**

```
impact = impressions × (median_ctr_at_position_5 − actual_ctr)
```

Target position 5 rather than 1 — projecting everything to first place inflates the total
into obvious fiction and destroys the credibility of the whole report. If a query is at 9
with strong topical authority, note a position-3 target explicitly instead of changing the
default silently.

**Grouping matters.** Aggregate striking-distance queries by landing page before reporting.
Fifteen queries on one page is a single piece of work, and presenting them as fifteen
findings misrepresents the effort.

## 3. CTR underperformance

Pages ranking adequately that fail to earn the clicks their position should produce. The fix
is usually a title and meta description rewrite — cheap, fast, and independent of ranking.

**Inclusion:** impressions ≥100 in the window, position ≤20, and actual CTR at least 40%
below the property median for that position bucket.

The 40% floor exists because CTR is inherently noisy at low volume and varies legitimately
with intent — an informational query will underperform a navigational one at the same
position for reasons no title rewrite will fix. A gap under 40% is usually intent mix rather
than a defect.

**Before recommending a rewrite, check the alternative explanations**, or the
recommendation will be wrong roughly half the time:

- **SERP feature absorption.** A featured snippet, AI Overview, People Also Ask block, or
  shopping carousel above the organic result suppresses CTR regardless of the title. Check
  `searchAppearance` and, where possible, look at the live SERP.
- **Brand mismatch.** Queries where the user wants a different brand will never convert.
- **Intent mismatch.** A transactional query landing on a blog post has a content problem,
  not a title problem.

Say which explanation you concluded and why. "Rewrite the title" attached to a query being
eaten by an AI Overview is the kind of recommendation that makes clients stop reading.

## 4. Keyword cannibalization

Two or more URLs competing for the same query. Real cannibalization splits link equity and
destabilizes ranking; apparent cannibalization is often just normal topical overlap, and
consolidating on it destroys working pages.

**Inclusion:** for a single query with ≥100 impressions over 90 days, two or more URLs each
holding ≥15% of that query's impressions.

**Confirmation — require at least one of these before calling it cannibalization:**

- The URL Google ranks for the query **alternates** across the window. This is the strongest
  signal: it means Google is uncertain which page to serve.
- Both URLs sit at position >10 while the query's total impressions suggest it should rank
  better.
- The two pages have near-duplicate titles or primary headings.

**Do not flag** a category page and a product page ranking for the same query, or a hub and
a spoke both appearing — that is intended architecture. Impression share alone is not
evidence; alternation is.

**Resolution options, in order of preference:** differentiate the two pages' intent and
internal anchors; consolidate the weaker page into the stronger with a 301; or canonicalize
one to the other if both must exist for users. Recommend the specific one, with the reason.

## 5. Traffic decay with seasonality control

Requires pulls A (current 28d), B (previous 28d), and C (same 28d last year).

**Inclusion:** pages where clicks fell ≥25% period-over-period with ≥50 clicks in the
baseline period. The volume floor matters — a drop from 4 clicks to 1 is a 75% decline and
means nothing.

**Classification is the whole value of this module.** Apply the diagnostic table in SKILL.md
Step 5 to each declining page using all three metrics, then check the year-over-year pull
before finalizing. If the same decline appears in the same weeks last year, it is seasonal
and the recommendation is to wait — writing that down is more useful than manufacturing a
fix, and it is the finding clients most often have never been told.

Also scan pull D (16 months by date) for **step changes** rather than gradual slopes. A cliff
on a single date points at something discrete — a migration, a redirect change, a robots
edit, a manual action, or a core update. Name the date; it makes the cause findable.

## 6. Index coverage

Bounded by the URL Inspection quota (2,000/day/property — see
`references/gsc-api-surface.md`), so this is a sampling exercise. Compare three sets:

- URLs in the sitemaps (`sitemaps.list`, then fetch the sitemap files).
- URLs with impressions in the window (pull A) — proof Google has them indexed.
- URLs found by crawling the site.

The interesting findings are the gaps:

| Gap | Meaning |
|---|---|
| In sitemap, no impressions, verdict not indexed | Discovery or quality problem — the core index finding |
| In sitemap, indexed, no impressions | Indexed but non-competitive; a content problem, not technical |
| Crawlable on site, absent from sitemap | Discovery gap; usually a trivial fix |
| Has impressions, absent from sitemap | Sitemap is stale or incomplete |
| Indexed, but Google-selected canonical ≠ declared canonical | Canonicalization conflict; check the pair |

That last row deserves particular attention — it is invisible without URL Inspection and
frequently explains otherwise inexplicable ranking behavior.

Always report sample size and how URLs were selected.

## 7. Device divergence

From pull E (`page` + `device`).

**Inclusion:** pages where impression-weighted mobile position is ≥3 worse than desktop, with
≥100 impressions on each device.

A gap that size is rarely a coincidence. Look for mobile-specific causes: content hidden
behind interaction on small viewports, interstitials, layout shift, slow mobile LCP, or
resources blocked to mobile crawlers. Since Google indexes mobile-first, a mobile-specific
defect caps the page's ceiling everywhere.

Remember to weight by impressions when computing each device's position (caveat 2).

## 8. Intent drift and zero-click pages

Two related patterns, both about mismatch rather than volume.

**Intent drift:** pull the top 10 queries by impressions for each significant page. When the
page's highest-impression queries do not match what the page is actually about, Google is
matching it to demand it cannot satisfy — which shows up as high impressions with poor CTR.
The fix is either to serve that intent properly or to build a separate page for it. This
module needs judgment about what each page is *for*, so it cannot be scripted.

**Zero-click pages:** impressions ≥500, clicks ≤5, position ≤10. Ranking on page one and
earning nothing almost always means the SERP answers the query without a click — an AI
Overview, a featured snippet held by someone else, or a definitional query. Verify against
the live SERP before recommending anything, and be willing to conclude that the query is
not winnable. Recommending a title rewrite for a query Google answers inline wastes the
user's time.
