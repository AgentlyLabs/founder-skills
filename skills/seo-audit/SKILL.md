---
name: seo-audit
description: Run a rigorous SEO audit on a real website using Google Search Console data pulled through an MCP connector, combining GSC performance analysis (striking-distance queries, CTR gaps against the site's own position curve, keyword cannibalization, traffic-decay diagnosis, index coverage) with on-page and technical best-practice checks, then produce a prioritized report with estimated click impact. Use this whenever the user wants an SEO audit, site audit, or "SEO review"; asks why their organic traffic, clicks, impressions, or rankings dropped or went flat; asks which pages or keywords to fix, improve, or prioritize; mentions Google Search Console or GSC at all; asks about indexing or coverage problems, canonicalization, crawl issues, cannibalization, low CTR, titles and meta descriptions, striking-distance or "almost ranking" keywords, Core Web Vitals, or sitemap health. Trigger even when the user never says the words "SEO" or "audit" — "why did my Google traffic tank last month", "which blog posts should I update", and "pull my Search Console data and tell me what's wrong" are all this skill.
---

# SEO Audit via Google Search Console

## Why this skill exists

Most SEO audits fail in one of two ways. They either dump every crawler warning into a
200-row spreadsheet with no sense of what actually costs money, or they assert causes
("your rankings dropped because of the algorithm update") that the available data cannot
support.

This skill exists to avoid both. The core discipline is: **every finding is tied to
measured GSC data, states the mechanism behind it, and carries an impact estimate whose
arithmetic is shown so the user can disagree with it.** A finding you cannot quantify or
explain is an observation, not a recommendation, and belongs in an appendix.

The second discipline is honesty about what Search Console can and cannot tell you. A
large fraction of published "GSC audit" advice quietly assumes data the API does not
expose. Getting this wrong produces confident, wrong conclusions — see
`references/gsc-api-surface.md` for exactly where the boundaries are.

## Step 0 — Find the Search Console connection

There is no single canonical GSC MCP server, so do not assume tool names. Discover them:

1. Search for the tools with `ToolSearch` using queries like `search console`,
   `+searchconsole`, `google seo analytics`. Load whatever matches.
2. If nothing loads, check the MCP registry (`search_mcp_registry` with keywords like
   `["google search console", "seo"]`) and surface connect options with
   `suggest_connectors`.
3. Confirm which properties the connection can actually see before planning anything —
   the equivalent of `sites.list`. Property type matters: a **domain property**
   (`sc-domain:example.com`) aggregates all subdomains and protocols, a **URL-prefix
   property** (`https://example.com/`) does not. Auditing a URL-prefix property and
   reporting it as whole-site truth is a common and invisible error.

If no GSC connection exists, say so plainly and offer the fallback: a
best-practice-only audit from crawling the live site (Step 4), clearly labeled as having
no performance data behind it. Do not silently degrade into a generic checklist — the
user asked for an audit grounded in their data, and they should know if they aren't
getting one.

**If the GSC MCP exposes write operations** (submitting sitemaps, requesting indexing,
deleting properties), treat them as outward-facing changes to the user's live search
presence and confirm before calling them. Reading is the whole job here; writing is not.

## Step 1 — Scope before pulling

Ask, or infer from context, only what changes the analysis:

- **Which property**, and its type (domain vs URL-prefix).
- **The question behind the request.** "Traffic dropped" is a diagnosis job and needs
  period-over-period plus year-over-year windows. "What should I work on" is an
  opportunity job and needs a single recent window at query+page granularity. These
  produce different reports; guessing wastes a lot of pulling.
- **Search type and market.** Default `type=web`. If the site is image- or video-led, or
  has meaningful non-English markets, filter by country rather than blending markets —
  averaged position across countries is close to meaningless.
- **Section scope.** For large sites, a path filter (`/blog/`, `/products/`) produces a
  far more actionable audit than a whole-property average.

## Step 2 — Pull the data

Read `references/gsc-api-surface.md` before the first query. It documents the exact
methods available, the row limits and pagination behavior, and five data caveats that
will silently corrupt your numbers if ignored — most importantly anonymized queries,
impression-weighted position averaging, and the freshness lag.

The standard pull set for a full audit:

| Pull | Dimensions | Window | Purpose |
|---|---|---|---|
| A | `page`, `query` | last 28 days | Opportunity + cannibalization core |
| B | `page`, `query` | previous 28 days | Period-over-period delta |
| C | `page`, `query` | same 28 days, prior year | Seasonality control |
| D | `date` | last 16 months | Trend shape, step-change detection |
| E | `page`, `device` | last 28 days | Mobile/desktop divergence |
| F | `query`, `country` | last 28 days | Market mix, if multi-market |

Paginate to exhaustion rather than taking the first page — `rowLimit` caps at 25,000 and
truncated data biases every ranked list toward whatever the API happened to return first.
Use `dataState=final` for anything you compare across periods, so a partial most-recent
day doesn't manufacture a fake decline.

## Step 3 — Run the analyses

`references/analyses.md` specifies eight analysis modules with their thresholds, ranking
formulas, and the reasoning behind each cutoff. Read it and work through the modules that
fit the scope from Step 1.

`scripts/analyze_gsc.py` implements the deterministic ones — CTR-curve construction,
striking distance, cannibalization, and decay classification. Prefer it over
recomputing by hand: the math is fiddly, the script is tested against the caveats in the
reference doc, and it keeps results reproducible across runs.

```bash
python3 scripts/analyze_gsc.py --current pull_a.json --previous pull_b.json \
    --year-ago pull_c.json --out findings.json
```

It accepts raw GSC API response shapes (`{"rows": [{"keys": [...], "clicks": ...}]}`) and
emits ranked findings. Pass `--help` for the full flag set.

One methodological note worth internalizing: the script builds the **expected CTR curve
from the property's own data** — the median CTR at each integer position across the site —
rather than applying published industry CTR benchmarks. Those benchmarks vary wildly by
SERP layout, brand strength, and query intent, so importing them produces confident
nonsense. A site compared against itself yields a defensible gap.

## Step 4 — Add the on-page and technical layer

GSC tells you how pages perform, not why the HTML is wrong. `references/onpage-checks.md`
lists the checks worth running by fetching the actual pages, ordered by how often they
turn out to matter. Concentrate on the pages the Step 3 analyses flagged rather than
crawling everything — a check on a page with no impressions has no impact to estimate.

Core Web Vitals are **not** in the Search Console API. Get field data from the CrUX API or
PageSpeed Insights API, and label it as such in the report.

## Step 5 — Diagnose, don't just list

For every page or query with a decline, the combination of the three metrics identifies
the mechanism. This table is the analytical core of the audit:

| Clicks | Impressions | Position | Mechanism | Where to look |
|---|---|---|---|---|
| ↓ down | → flat | → flat | CTR loss — SERP layout, AI Overview, or title change | Title/meta, SERP features, competitor snippets |
| ↓ down | ↓ down | ↓ worse | Genuine ranking loss | Content freshness, lost links, competitor gains |
| ↓ down | ↓ down | → flat | Demand loss or seasonality | Compare year-over-year before acting |
| → flat | ↑ up | ↓ worse | Broader but weaker matching | New irrelevant queries diluting the average |
| ↓ down | → flat | ↓ worse | Rank slide within page 1 | Often precedes a larger drop; act early |

The year-over-year pull exists specifically to stop the third row being misdiagnosed as
the second. Seasonal declines get "wait" as a recommendation, and saying so builds more
trust than inventing a fix.

## Step 6 — Prioritize by impact over effort

Estimate incremental monthly clicks for each finding and **show the arithmetic inline**:

> `/guides/onboarding` — 4,200 impressions/mo at position 11.3, CTR 0.9%. Median CTR at
> position 5 across this property is 4.1%. Moving to position 5 ≈ 4,200 × (0.041 − 0.009)
> ≈ **+134 clicks/mo**. Effort: M (needs ~600 words and 3 internal links).

Two rules keep these estimates from becoming fiction. Use the site's own CTR curve, never
an imported one. And when a projection depends on a rank improvement you cannot guarantee,
state the assumed target position rather than hiding it inside a single number.

Rank findings by impact ÷ effort. Lead the report with the three highest-leverage items,
not the most numerous category of warning.

## Step 7 — Write the report

Use the structure in `references/report-template.md`. It front-loads an executive summary
a non-specialist can act on and pushes methodology to an appendix, because the person
deciding whether to fund the work is rarely the person implementing it.

Always include the data-caveats appendix. It states the window, the property type, the
freshness lag, and the anonymized-query gap. This is what makes the numbers auditable
later, and it is the difference between a report that survives scrutiny and one that
gets quietly distrusted.

## Honesty rules

These matter more than any individual analysis, because an audit's only real product is
trust in its conclusions.

- **Never fabricate a metric.** If a pull failed or returned nothing, say the analysis
  could not be run. An empty result is a finding.
- **Distinguish measured from inferred.** "Clicks fell 34%" is measured. "Because of the
  March core update" is a hypothesis — label it and give the evidence for and against.
- **Report the anonymized-query gap.** Query-dimension clicks always sum to less than
  property totals because GSC withholds rare queries. Don't reconcile them; state the gap.
- **Don't recommend at unsupported precision.** With 40 impressions in 28 days there is no
  CTR signal. Set minimum-volume thresholds and exclude what falls below them.
- **Flag when the property type limits the conclusion.** A URL-prefix property blind to
  `www` or `http` variants cannot support whole-site claims.

## Reference files

- `references/gsc-api-surface.md` — available methods, quotas, and the five data caveats.
  Read before the first pull.
- `references/analyses.md` — the eight analysis modules, thresholds, ranking formulas.
- `references/onpage-checks.md` — technical and on-page checks, by expected impact.
- `references/report-template.md` — output structure.
- `scripts/analyze_gsc.py` — deterministic analysis over raw GSC responses.
