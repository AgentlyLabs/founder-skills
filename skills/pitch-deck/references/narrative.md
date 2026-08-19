# Narrative

Read this before building anything. The design system is reusable; the argument is not, and
the argument is what gets funded.

## Contents

- [The eleven-slide arc](#the-eleven-slide-arc)
- [Headline craft](#headline-craft)
- [Body copy rules](#body-copy-rules)
- [The proof-point strip](#the-proof-point-strip)
- [Adapting the arc by stage](#adapting-the-arc-by-stage)

## The eleven-slide arc

Eleven slides, each with a job and a characteristic failure. The count is a constraint on
purpose: it forces every slide to justify itself.

| # | Slide | Job | Usual failure |
|---|---|---|---|
| 01 | Cover | Say what the company does in one line | A tagline that could describe five companies |
| 02 | Problem | Make the pain visceral and specific | Describing a market condition instead of somebody's bad day |
| 03 | The bet | Why this wins, and why now | No "why now", so the company reads as arbitrary |
| 04 | What we built | The architecture in one picture | A feature list wearing a diagram's clothes |
| 05 | Pillar 1 | The hardest thing you built | Explaining how it works instead of why it's hard |
| 06 | Pillar 2 | The second differentiator | Padding — a pillar that is really a feature |
| 07 | Pillar 3 | The third, or the output layer | Same |
| 08 | Market | Size it credibly, bottom-up | Top-down "1% of a $50B market" |
| 09 | Traction | Evidence, at whatever scale is real | Vanity metrics, or hiding smallness |
| 10 | Team | Why *you* specifically | Logo soup with no causal link to this problem |
| 11 | Vision | What the world looks like if you win | Restating the product |

### Slide 01 — Cover

Logo, one positioning line, chrome. Nothing else.

The line must pass this test: **could a competitor put their name on it?** If yes, rewrite. It
should name the user, the thing being replaced, or the specific mechanism. Structure that
works well: a short declarative fragment, then the payload in accent —
`Your stack. Your data. **One AI workspace that does the work.**`

### Slide 02 — Problem

The rule: **one person's specific bad hour, not an industry trend.** Trends are
unfalsifiable and boring. A concrete sequence of actions with timestamps is neither.

This is the best slide in the deck for an artifact — a log, a timeline, a screenshot of the
workaround people currently suffer through. Quantify the cost in a unit the reader feels:
hours per week, headcount, dollars per month. Then show the repetition, because frequency is
what turns an annoyance into a market.

### Slide 03 — The bet

The thesis slide, and the one most decks skip. It answers: what do you believe that the
market has not priced in yet, and what changed recently to make it true?

Best delivered as a **statement slide** — headline, two lines of body, a proof-point strip.
No artifact. The visual restraint signals that the idea is load-bearing.

Strong shape: a reversal. `The model isn't the moat. **Your stack is.**` It names the
consensus view and displaces it in one breath.

### Slide 04 — What we built

One picture of the whole system. Not a feature list. The reader should be able to trace data
from an input to an output with their finger.

Use the **diagram** archetype: external systems as chips around the edge, your product as a
container in the middle, connectors showing direction. Highlight the single component that is
genuinely hard to build. A legend strip at the bottom explains what the connector lines mean.

### Slides 05–07 — The pillars

One per differentiator, each on a **split** layout. The discipline: each pillar is something a
competitor would need a year to replicate. If a pillar is really a feature, cut it and run a
ten-slide deck. Ten strong slides beat eleven with one padded.

Headline each pillar as a **capability with a claim in it**, not a component name. "A
knowledge graph that builds itself" earns attention; "Knowledge Graph" does not. Put a number
under the body copy — nodes, latency, throughput, whatever is real.

### Slide 08 — Market

**Bottom-up only.** Segment by customer type, and for each show count of customers, realistic
annual price, and the product. Then total it. A reader can check bottom-up arithmetic, which
is exactly why it is persuasive; "1% of a huge market" invites disbelief because it cannot be
checked.

Highlight the beachhead segment, not the biggest one. Which segment you *start* with tells
the reader whether you have thought about sequencing.

Use the **ranked rows** archetype: one row per segment, proportional bars, big number right.

### Slide 09 — Traction

Whatever is real, framed honestly. Three metrics maximum, on the **metric trio** archetype.

Small numbers presented confidently read far better than medium numbers inflated. `40 users,
cohort 1 complete` with a real conversion story beats "thousands of signups" that nobody
believes. If growth is the story, show two points and the multiple between them. Date-stamp
the slide — an undated traction slide is assumed stale.

### Slide 10 — Team

For each founder: name, role, and a bio whose every clause connects to *this* problem.
Prestige alone is not an argument. "Shipped enterprise systems at a large software company —
the exact stack this product lives or dies on" is an argument, because it draws the causal
line.

If the founders have history together, show it. A timeline strip of years working together
de-risks the team more than any individual credential, because founder breakup is the most
common early failure mode and you are pre-empting it.

### Slide 11 — Vision

One sentence about the world if you win, not about the product. Test: does it describe a
changed state of affairs, or a feature? Centered, large, accent on the final clause. Logo,
URL, and stop.

## Headline craft

The headlines are the deck. Rules, in order of impact:

**1. Write a complete declarative sentence with a period.** `Demand is louder than we
expected.` Fragments and label-headlines (`Our Market`, `The Team`) waste the most valuable
line on the slide.

**2. Five to nine words.** Longer and it stops being a headline; shorter and it usually
lacks a verb.

**3. Include a turn.** The best headlines set up an expectation and break it: `Your AI starts
every day at zero.` `Eight years co-founding. One product the work pointed to.` The turn is
what makes it memorable.

**4. Put the accent gradient on the payload.** The accented words should carry the claim on
their own.

**5. No feature nouns as headlines.** `Knowledge Graph` is a label. `A knowledge graph that
builds itself` is a claim. Claims can be argued with, which means they can be believed.

**6. Read all eleven in sequence.** They should form a paragraph that makes the whole
argument. This is the test that catches structural problems while they are still cheap to
fix.

## Body copy rules

- **Two to three sentences. Maximum.** If it needs four, the headline is underspecified or
  the slide is doing two jobs.
- **Bold the claim, not keywords.** One bolded phrase per paragraph, on the thing you want
  repeated back to you. Scattered bold is the same as no bold.
- **Concrete nouns over category nouns.** "Slack, Stripe, Linear" beats "your business tools"
  — specificity is the cheapest available credibility.
- **Numbers in the body, not just in metrics.** A number inside a sentence does more work than
  the same number in a stat tile, because it is attached to a claim.
- **No adjective stacking.** "Powerful, intuitive, enterprise-grade" is invisible. One precise
  verb beats three adjectives.

## The proof-point strip

A recurring device: a hairline rule with two or three mono uppercase items spread across the
slide width, the rightmost brighter than the others.

```
MODELS COMMODITIZED IN 18 MONTHS    MCPS OPENED EVERY STACK    CONTEXT COMPOUNDS — AND NEVER RESETS.
```

It works because the reader takes it as a machine-generated footnote rather than marketing
copy, so it clears their defenses. The rightmost item, brighter, is the punchline — put the
inference there and the supporting facts to its left. Keep each item under about eight words.

Use it on statement slides that have no artifact, where it does the visual work a diagram
would otherwise do.

## Adapting the arc by stage

**Pre-seed.** The arc as written. Thesis and team carry the weight; traction can be a
waitlist. The bet slide is the most important in the deck.

**Seed.** Same shape, but slide 09 needs retention or revenue, not just signups. Add a slide
between 09 and 10 on go-to-market motion if a repeatable channel exists.

**Series A and later.** Add two slides and accept thirteen:

- **Competition**, after the pillars. Use ranked rows with your axis of differentiation as the
  bar, not a checkbox grid — grids invite feature shopping and you will lose that comparison
  to whoever has more checkboxes.
- **Financials**, after traction. Historical revenue plus a plan tied to the raise. Metric
  trio for headline numbers; put the model in an appendix rather than on the slide.

Never silently drop these from a later-stage deck. If the user is raising a Series A without
them, say so — an investor will ask within the first five minutes, and it is better to hear
it from you.
