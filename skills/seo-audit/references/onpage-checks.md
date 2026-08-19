# On-page and technical checks

GSC explains how pages perform; it cannot tell you what is wrong with the HTML. These checks
require fetching the actual pages.

Run them on the pages the performance analyses flagged, not on the whole site. A defect on a
page with no impressions has no impact to estimate, and a report padded with such findings
buries the ones that matter.

Ordered by how often each turns out to actually explain something.

## Tier 1 — usually explains a real performance problem

**Indexability conflicts.** A page can be blocked in four independent ways, and they
routinely contradict each other: `robots.txt` disallow, `<meta name="robots" content="noindex">`,
an `X-Robots-Tag` HTTP header, and a canonical pointing elsewhere. Check all four. The
classic failure is a page blocked in `robots.txt` *and* carrying `noindex` — Google cannot
crawl it, therefore never sees the `noindex`, and may index it from links anyway.

**Canonical correctness.** Every indexable page should declare a self-referencing canonical
with an absolute URL. Compare the declared canonical against Google's selected canonical from
URL Inspection — a mismatch means Google disagreed with the site, and that disagreement is
usually the entire explanation for a page underperforming.

**Title tags.** One per page, unique across the site, front-loading the primary query, roughly
50–60 characters before Google truncates. Duplicate titles across pages both cause
cannibalization and waste the highest-leverage on-page element there is.

**Redirect chains and status codes.** Every internal link should resolve in one hop to a 200.
Chains dilute signals and slow crawling; internal links to 404s and 301s are pure waste and
trivially fixable.

**Internal link depth.** Pages more than three clicks from the homepage get crawled less and
rank worse. Orphan pages — reachable only from the sitemap — are the extreme case and are
common on sites with programmatic content.

## Tier 2 — worth checking, moderate hit rate

**Meta descriptions.** Not a ranking factor, but directly drives CTR, which makes them the
cheapest fix for the module-3 findings. Aim for ~150–160 characters, unique, written as ad
copy rather than a summary. Google rewrites them often; that is fine, a good one still wins
frequently enough to matter.

**Heading structure.** One `<h1>` matching the page's primary intent, with `<h2>`/`<h3>`
forming a logical outline. Skipped levels matter far less than a missing or generic `<h1>`.

**Structured data.** Validate against Schema.org and check for eligibility errors. Correct
markup unlocks rich results; invalid markup silently earns nothing. Match the type to the
content — `Article`, `Product`, `FAQPage`, `BreadcrumbList` — and never mark up content that
is not visible on the page.

**Hreflang reciprocity.** For multi-language sites, every hreflang annotation must be
reciprocal and include a self-reference, with valid language-region codes. Non-reciprocal
annotations are ignored entirely, which is a silent failure mode.

**Core Web Vitals.** Not available from the Search Console API — pull field data from the
CrUX API or PageSpeed Insights API and label the source. Current thresholds: LCP ≤2.5s,
INP ≤200ms, CLS ≤0.1, at the 75th percentile. Prefer field data over lab scores; a 98 lab
score with failing field data means real users are having a worse time than the test.

**Thin and duplicate content.** Pages with little unique value, or near-duplicates across
templated sections. Judge against what the query needs, not an arbitrary word count.

## Tier 3 — check when the basics are clean

- `robots.txt` reachable, returns 200, does not block CSS or JS needed for rendering.
- XML sitemaps: valid, under 50,000 URLs and 50MB uncompressed per file, listing only
  canonical 200-status URLs, referenced from `robots.txt`.
- HTTPS everywhere, with no mixed content and a single canonical host — one of
  `www`/non-`www` redirecting to the other.
- Image `alt` text that describes the image, plus modern formats and explicit dimensions.
- Pagination handled with real crawlable links rather than JavaScript-only controls.
- Faceted navigation not generating unbounded crawlable URL combinations.

## A note on JavaScript rendering

If the site renders content client-side, check what Google actually sees rather than what the
browser shows. Fetch the raw HTML and compare it to the rendered DOM. Content that exists
only after hydration may be indexed late or not at all, and this single issue can invalidate
every other on-page conclusion — so check it early on JS-heavy sites.
