# Page checks

Every check states its **scope** (which page types it applies to), its **threshold and
the reasoning behind that threshold**, **how to measure it**, and the **measurement key**
it writes into `measurements.json`. Findings in the report cite those keys.

Thresholds here are calibrated defaults, not constants. When a site's context makes one
wrong, change it and say in the report that you did.

Scope tags: `LP` dedicated landing page · `HOME` homepage · `PRICING` · `FORM` any page
with a conversion form · `ALL`.

---

## Tier 1 — measure these first

### 1. Message match `LP`

**Key:** `match.score`, `match.missing_terms`, `match.h1`, `match.source_copy`

The visitor's expectation was set by an ad, an email, or a search result seconds ago. The
H1 must visibly restate that promise, using the same nouns.

**Measure:** `scripts/measure.py --source-copy "<the ad headline or query>"`. It extracts
content words from the source, strips stopwords, and reports which appear in the H1,
subhead, or first paragraph.

**Threshold:** every *primary noun* in the source promise must appear in the H1 or
subhead. Not paraphrased — the same word. If the ad says "invoice reconciliation" and the
H1 says "financial operations, simplified", that is a miss even though it is arguably the
same thing. The visitor is pattern-matching in under a second and does not do synonym
resolution.

**Why this threshold:** the check is deliberately literal, because the failure mode is a
marketing team that believes its abstraction is obvious. If a synonym genuinely reads as
a match to a stranger, note the exception explicitly rather than loosening the rule.

**Does not apply to** homepages or organic-navigation traffic, where there is no single
promise to match. Do not run it there.

### 2. Value proposition legibility `ALL`

**Key:** `hero.h1`, `hero.h1_word_count`, `hero.subhead`, `hero.subhead_word_count`,
`hero.category_noun`

A stranger, given five seconds, should be able to say what this is, who it is for, and
what changes for them.

**Measure:** script extracts H1 and the first subhead. Then run the five-second test
yourself against the mobile screenshot — read it once, look away, write down what the
product does. If you cannot, that is the finding, and it is usually the most valuable one
in the report.

**Threshold:** the H1 or subhead must contain a **concrete category noun** — the thing it
actually is. "Invoice reconciliation for Shopify sellers" passes. "Transform your
financial workflow" does not, and neither does "The future of work." Subhead ≤ 25 words.

**Why:** abstraction in a headline is nearly always a symptom of unresolved positioning
rather than a copy problem, and reporting it as a copy problem produces a rewrite that
fails the same way. If the H1 is vague, ask whether the team can name the category.

### 3. Form field inventory `FORM`

**Key:** `form.field_count`, `form.required_count`, `form.fields`, `form.submit_label`

**Measure:** script inventories every input, select, and textarea with its `name`,
`type`, `required`, `autocomplete`, and label text.

**Threshold:** each field must pass one of two tests — *we cannot deliver the promised
thing without it*, or *a human will act on it within 48 hours*. Fields that pass neither
are the finding, reported as a count and a list, not as "your form is too long."

**Why this framing:** field count alone is not actionable and the "each field costs 10%"
figure is folklore (see `evidence-base.md`). "These six fields are not needed to send a
PDF" is a decision someone can make in a meeting.

Common failures: phone number on a content download, company size on a free trial,
"how did you hear about us" ahead of the conversion rather than after it, and a required
field that the backend does not store.

### 4. Mobile input configuration `FORM`

**Key:** `mobile.input_type_errors`, `mobile.autocomplete_missing`, `mobile.viewport_meta`

**Measure:** script, from the HTML.

**Threshold, all mandatory:**

- email fields use `type="email"`, phone `type="tel"`, numeric `inputmode="numeric"`
- every field carries a valid `autocomplete` token (`email`, `given-name`, `tel`,
  `organization`, `cc-number`…)
- `<meta name="viewport" content="width=device-width, initial-scale=1">` present, and
  **no** `user-scalable=no` or `maximum-scale=1` — those break zoom for anyone who needs it
- every input has an associated `<label>`, not just a placeholder

**Why mandatory rather than a test:** these are defects, not preferences. Wrong keyboard,
no autofill, and a form that cannot be zoomed make the task measurably harder on the
device most of the traffic uses. Ship the fix; do not spend an experiment slot on it.

### 5. Attention ratio `LP`

**Key:** `attention.links`, `attention.goals`, `attention.ratio`, `attention.nav_links`,
`attention.footer_links`

Links on the page divided by conversion goals.

**Measure:** script counts unique in-page destinations, split by nav / body / footer.

**Threshold:** on a dedicated landing page built for one action, target 1:1 and treat
anything above about 5:1 as a finding. The usual culprit is the site's global nav and
footer being included on a page whose only job is one conversion.

**Why the scope tag matters:** this check is **wrong on homepages**, where navigation is
the point, and wrong on docs, blog, and pricing pages. Applying it everywhere is the most
common way an automated CRO report discredits itself. It is a heuristic from landing page
practice, not a measured law — treat it as a prompt to ask "why is this link here", not
as a score.

### 6. Cost and commitment are stated `LP` `PRICING`

**Key:** `price.on_page`, `price.pricing_link`, `price.trial_stated`,
`price.card_required_stated`

**Measure:** script scans for currency patterns, a link to a pricing page, and phrases
covering trial length and card requirement.

**Threshold:** at minimum the page must answer, without a click: does this cost money,
roughly how much or where to find out, and what am I committing to right now. A free
trial page that does not say whether a card is required is the highest-frequency instance.

**Why:** unresolved cost is not a persuasion problem, it is an unanswered question, and
unanswered questions at the decision point are where people leave. Note that "publish
your pricing" is *not* the recommendation for genuinely enterprise sales — the finding is
that the question is unanswered, and the fix may be a range, a starting price, or an
explicit "pricing depends on seats, here is the model."

### 7. Trust at the point of commitment `FORM`

**Key:** `trust.markers`, `trust.distance_to_submit`

**Measure:** script locates trust markers (security/privacy statements, guarantees,
"no credit card", customer counts, review badges) and reports the DOM distance from the
primary submit control to the nearest one.

**Threshold:** at least one relevant assurance within the same form container. Proximity
is the check — a footer badge and a badge beside the button are different interventions.

### 8. Rendered fold and occlusion `ALL`

**Key:** `cta.above_fold_375`, `cta.above_fold_1366`, `cta.occluded`, `hero.visible_words`

Only a browser can answer these. With the page loaded via `preview_start`:

```javascript
(() => {
  const btn = document.querySelector('SELECTOR_FOR_PRIMARY_CTA');
  if (!btn) return { error: 'primary CTA selector did not match' };
  const r = btn.getBoundingClientRect();
  const centre = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  const hit = document.elementFromPoint(centre.x, centre.y);
  return {
    viewport: { w: innerWidth, h: innerHeight },
    cta_top_px: Math.round(r.top + scrollY),
    folds_down: +((r.top + scrollY) / innerHeight).toFixed(2),
    cta_size: [Math.round(r.width), Math.round(r.height)],
    occluded: !(hit === btn || btn.contains(hit)),
    occluded_by: hit && hit !== btn && !btn.contains(hit)
      ? (hit.tagName + '.' + (hit.className || '').toString().slice(0, 60)) : null,
    horizontal_overflow: document.documentElement.scrollWidth > innerWidth + 1
  };
})()
```

**`occluded` is the highest-value line here.** A cookie banner, a chat bubble, or a
sticky promo bar sitting on top of the primary button is invisible in every static
analysis and catastrophic in reality. Check it at 375×812 specifically — that is where
overlays collide.

**Threshold:** primary CTA within the first 1.5 viewport heights on a page for
high-intent traffic; occlusion is always a defect; horizontal overflow is always a defect.

### 9. Tap targets and contrast `ALL`

**Key:** `mobile.tap_targets_under_44`, `cta.contrast_ratio`

At the 375-wide viewport:

```javascript
(() => {
  const lum = c => {
    const [r, g, b] = c.match(/\d+\.?\d*/g).slice(0, 3).map(v => {
      v = v / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const bgOf = el => {
    for (let n = el; n; n = n.parentElement) {
      const c = getComputedStyle(n).backgroundColor;
      if (c && !/rgba?\(0, 0, 0, 0\)|transparent/.test(c)) return c;
    }
    return 'rgb(255,255,255)';
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
    return +((x + 0.05) / (y + 0.05)).toFixed(2);
  };
  const btn = document.querySelector('SELECTOR_FOR_PRIMARY_CTA');
  const small = [...document.querySelectorAll('a,button,input,select,[role=button]')]
    .map(e => ({ e, r: e.getBoundingClientRect() }))
    .filter(o => o.r.width > 0 && (o.r.width < 44 || o.r.height < 44))
    .map(o => ({
      tag: o.e.tagName,
      text: (o.e.innerText || o.e.value || '').trim().slice(0, 40),
      size: [Math.round(o.r.width), Math.round(o.r.height)]
    }));
  return {
    tap_targets_under_44: small.length,
    examples: small.slice(0, 10),
    cta_contrast: btn
      ? ratio(getComputedStyle(btn).color, bgOf(btn))
      : null
  };
})()
```

**Threshold:** tap targets ≥ 44×44 CSS px. CTA text contrast ≥ 4.5:1 against its own
background (WCAG AA), and the button itself visibly distinct from the page background.

**Report contrast, never color.** "Your CTA is 2.1:1 against its background" is a
measurement. "Try a red button" is folklore — see `evidence-base.md`.

### 10. Speed, from field data `ALL`

**Key:** `speed.lcp_field_ms`, `speed.inp_field_ms`, `speed.cls_field`,
`speed.transfer_bytes`, `speed.render_blocking`, `speed.requests`

**Measure:** the script records transfer weight, request count, and render-blocking
resources. For what users actually experience, pull the **CrUX API** (field data, real
devices) rather than a lab run:

```
https://chromeuxreport.googleapis.com/v1/records:queryRecord?key=API_KEY
{"url": "https://example.com/landing", "formFactor": "PHONE"}
```

If the URL has no CrUX data (too little traffic — common for exactly the sites that ask
for this audit), say so and fall back to origin-level data or to the transfer-weight
measurement, clearly labeled as a proxy.

**Threshold:** report the **75th percentile**, which is what CrUX gives you, not the
mean. LCP over 4s at p75 on phone is a real finding. LCP at 2.6s is not where this site's
conversion problem lives, and saying so keeps the report credible.

---

## Tier 2 — propose as experiments, not defects

Report these with the mechanism named and a test design attached, or as a judgment call
where traffic will not support a test. Never as "you must."

- **CTA label** `cta.primary_label` — states the outcome ("Get the audit") rather than the
  mechanic ("Submit") or the commitment the visitor has not made ("Buy now" on a first
  visit). Measure the label; propose alternatives.
- **CTA repetition** `cta.count`, `cta.distinct_labels` — one action, repeated at natural
  decision points, with the *same* label. Three different labels for the same action is a
  finding; a repeated CTA on a long page is not.
- **Social proof specificity** `trust.markers` — named person, role, and a concrete
  outcome beats anonymous volume. Audience mismatch actively hurts.
- **Page length and structure** `page.word_count` — not a threshold. Length made of filler
  loses; length that answers real objections wins.
- **Form structure** — multi-step vs single column, and whether progress is visible.
- **Pricing page tier count and anchoring** `PRICING`.

## Tier 3 — do not report

Button color, "above the fold" as a law, click-count reduction, exit-intent as a default,
generic urgency, heatmap aesthetics. `evidence-base.md` explains why each one is in this
list. Leaving them out is a feature of the report.

---

## Gaps to declare explicitly

If any of these could not be measured, list them in the report's gaps section rather than
silently omitting them. An unmeasured check is not a passed check.

- Page requires JavaScript to render its content — static extraction returns nothing and
  the browser layer is the only source.
- Page is behind auth, a paywall, or geo-gating.
- No traffic source supplied, so message match could not run.
- No CrUX record, so speed is lab or proxy only.
- No analytics access, so every finding is page-level and none is funnel-ranked.
