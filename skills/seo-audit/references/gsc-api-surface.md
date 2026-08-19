# What Search Console actually exposes

Read this before the first data pull. Most bad GSC audits are bad because they assume data
the API does not return, or because they average a metric that cannot be averaged.

## Contents

- [The four capability areas](#the-four-capability-areas)
- [searchanalytics.query in detail](#searchanalyticsquery-in-detail)
- [URL Inspection and its hard quota](#url-inspection-and-its-hard-quota)
- [Sitemaps](#sitemaps)
- [The five caveats that corrupt numbers](#the-five-caveats-that-corrupt-numbers)
- [What is NOT in the API at all](#what-is-not-in-the-api-at-all)
- [Mapping an unknown MCP to these capabilities](#mapping-an-unknown-mcp-to-these-capabilities)

## The four capability areas

The Search Console API surface is small. Whatever the MCP wrapper calls its tools, they
resolve to some subset of these:

| Area | Underlying methods | What you get |
|---|---|---|
| Properties | `sites.list`, `sites.get` | Which properties exist, permission level, property type |
| Performance | `searchanalytics.query` | Clicks, impressions, CTR, position by dimension |
| Per-URL index state | `urlInspection.index.inspect` | Index verdict, canonical, crawl, referring sitemaps |
| Sitemaps | `sitemaps.list`, `sitemaps.get` | Submitted sitemaps, counts, warnings, errors |

Write methods also exist (`sites.add`/`delete`, `sitemaps.submit`/`delete`). These change
the user's live search presence — confirm before calling any of them.

## searchanalytics.query in detail

**Dimensions:** `query`, `page`, `country`, `device`, `date`, `searchAppearance`.

**Metrics returned:** `clicks`, `impressions`, `ctr`, `position`.

**Key request fields:**

| Field | Notes |
|---|---|
| `startDate` / `endDate` | `YYYY-MM-DD`, inclusive. Max 16 months back. |
| `dimensions` | Array; combine freely except `searchAppearance` (see below). |
| `type` | `web` (default choice), `image`, `video`, `news`, `googleNews`, `discover`. |
| `dimensionFilterGroups` | Filter by page path, country, device, query substring/regex. |
| `aggregationType` | `auto`, `byPage`, `byProperty`. Changes what a row means. |
| `rowLimit` | Default 1,000. **Maximum 25,000.** |
| `startRow` | Zero-based offset for pagination. |
| `dataState` | `final` (default) or `all` (includes incomplete fresh days). |

**Pagination is mandatory, not optional.** Request `rowLimit=25000`, then keep advancing
`startRow` by 25,000 until a response returns fewer rows than requested. Stopping at the
first page silently truncates the dataset and biases every ranked list you build from it.

**`searchAppearance` cannot be grouped alongside other dimensions.** Query it on its own to
discover which appearance types the property has, then use a specific value as a *filter*
in combination with other dimensions.

**`aggregationType` changes the meaning of a row.** With `byPage`, metrics are deduplicated
per page — appropriate when you want page-level truth. With `auto` and a `query` dimension
present, you get query-level rows where the same page appears many times. Mixing the two in
one analysis double-counts impressions.

## URL Inspection and its hard quota

`urlInspection.index.inspect` returns, for a single URL: the index verdict, coverage state,
Google-selected canonical vs user-declared canonical, last crawl time, crawl-allowed and
indexing-allowed flags, referring sitemaps, and mobile-usability plus rich-results state.

**Quota: 2,000 queries per day per property, 600 per minute per property.**

This quota is the single biggest practical constraint on index-coverage auditing. There is
no bulk or aggregate index-coverage endpoint. So for any site above a couple thousand URLs,
inspect a **deliberate sample** and say so:

- Every URL flagged by the Step 3 performance analyses.
- All URLs with impressions but zero clicks over the window.
- A random sample of sitemap URLs with no impressions at all — these are where
  discovered-not-indexed and crawled-not-indexed problems hide.
- Templated sections: inspect a handful per template, since coverage problems are usually
  template-wide rather than page-specific.

Report the sample size and selection method. An index audit that implies full coverage from
200 inspections is misleading even when every individual verdict is accurate.

## Sitemaps

`sitemaps.list` gives submitted sitemaps with per-type submitted/indexed counts, warnings,
errors, last downloaded time, and whether a sitemap is pending. Useful signals:

- A sitemap not downloaded in weeks usually means a fetch error or an unreferenced file.
- A large gap between submitted and indexed counts is the cheapest available proxy for the
  index-coverage report — it does not tell you *why*, which is what URL Inspection is for.
- URLs live on the site but absent from any sitemap are a discovery problem worth flagging.

## The five caveats that corrupt numbers

**1. Anonymized queries.** Google withholds queries issued by very few users. Rows for them
simply do not appear in `query`-dimension results. Consequence: summing clicks across the
query dimension always yields **less** than the property total from a `date`-dimension
pull. This is expected behavior, not a bug and not something to reconcile. State the gap;
never present query-dimension sums as total traffic.

**2. Position cannot be plain-averaged.** The reported `position` is the average position of
the property's topmost result for that row. Averaging those averages across dates, pages,
or countries with equal weight gives a wrong answer. Always weight by impressions:

```
weighted_position = Σ(position_i × impressions_i) / Σ(impressions_i)
```

**3. Freshness lag.** Search Analytics data typically lags 2–3 days. With
`dataState=all`, the most recent day or two is partial, so any period-over-period comparison
that includes it manufactures a decline that does not exist. Use `dataState=final` for all
comparative work, and end windows at least 3 days before today.

**4. Property type scopes everything.** `sc-domain:example.com` covers all subdomains and
protocols; `https://example.com/` covers exactly that prefix. An audit of a URL-prefix
property is blind to `www`/non-`www` and `http`/`https` variants, which is precisely where
duplicate-content and canonicalization problems live. Check the type in Step 0 and carry
the limitation into the report.

**5. Averaged multi-market data is close to meaningless.** A page ranking 2nd in one country
and 40th in another reports as ~21st, which describes neither. If more than roughly 20% of
impressions come from outside the primary market, segment by country.

## What is NOT in the API at all

These appear in the Search Console web UI but have **no API endpoint**. Claiming to audit
them from the API is the most common false claim in GSC tooling:

| Not available | Get it from instead |
|---|---|
| Core Web Vitals / Page Experience report | CrUX API (field data) or PageSpeed Insights API |
| Page Indexing (coverage) report, in aggregate | Per-URL only, via URL Inspection, within quota |
| Links report (internal and external) | Your own crawl for internal; a third-party index for external |
| Crawl Stats report | Server logs |
| Manual Actions, Security Issues | UI only — ask the user to check and report back |
| Rich Results aggregate report | Per-URL via URL Inspection, or validate structured data directly |
| Removals, Video indexing, Merchant listings | UI only |

When the audit needs one of these, either pull it from the listed alternative and label the
source, or state that it requires the user to check the UI. Do not infer it.

## Mapping an unknown MCP to these capabilities

MCP wrappers differ in naming and granularity. Rather than guessing, load the tools and
read their schemas, then map each to an area above. Common patterns:

- A single broad `query_search_analytics` tool taking dimensions and dates — maps to
  `searchanalytics.query`. Check whether it exposes `rowLimit`/`startRow`; if it does not,
  it is probably capping results, so verify totals against a `date`-dimension pull before
  trusting any ranked list.
- Convenience tools like `get_top_queries` or `get_top_pages` — these are pre-baked
  `searchanalytics.query` calls, usually with a low row limit and no pagination. Fine for a
  quick look, insufficient for a full audit.
- An `inspect_url` tool — maps to URL Inspection; the 2,000/day quota still applies
  regardless of what the wrapper documents.

If a needed capability is missing from the connector, say which analysis it blocks rather
than substituting a weaker proxy without comment.
