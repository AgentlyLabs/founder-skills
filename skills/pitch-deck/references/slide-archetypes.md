# Slide archetypes

Eight layouts. Every slide should be one of them. The constraint is the point: a deck built
from eight repeating structures reads as designed, while a deck of eleven bespoke layouts
reads as assembled.

All eight are implemented as classes in `assets/deck.css`.

| Archetype | Class | Fits |
|---|---|---|
| 1. Cover | `.s-cover` | Opening slide |
| 2. Statement | `.s-statement` | Thesis, "why now", any pure-argument slide |
| 3. Split | `.s-split` | Product slides — the workhorse |
| 4. Diagram | `.s-diagram` | Architecture, system overview |
| 5. Ranked rows | `.s-rows` | Market segments, competition, anything ordered |
| 6. Metric trio | `.s-metrics` | Traction, financial headlines |
| 7. Profiles | `.s-profiles` | Team, advisors, customers |
| 8. Closing | `.s-closing` | Vision, final slide |

## 1. Cover

Centered logo, one positioning line, chrome top and bottom. The bottom chrome carries domain
and contact — the only slides where bottom chrome appears are this one and the closing.

Vertically centered, but with the optical center slightly above true center (roughly 45% of
height), because a block centered mathematically reads as low.

## 2. Statement

Eyebrow, large headline, two lines of body, then a proof-point strip at the bottom of the
content band. **No artifact** — the emptiness is the design.

The most under-used archetype. Reach for it when the slide's job is to make the reader accept
an idea rather than understand a mechanism. A statement slide between two dense ones also
resets the reader's attention, which is why decks that are dense on every slide are exhausting
to read.

Headline can run wide here — up to about 75% of slide width across two lines.

## 3. Split

The workhorse. Copy left at 40%, artifact right at 55%, 5% gutter.

```
┌──────────────────────────────────────────────┐
│ SECTION                              05 / 11 │
│                                              │
│   EYEBROW · LABEL      ┌───────────────────┐ │
│   Headline that        │                   │ │
│   makes a claim.       │     artifact      │ │
│                        │                   │ │
│   Two or three         │                   │ │
│   sentences of body.   └───────────────────┘ │
│                                              │
│   metric · metric                            │
└──────────────────────────────────────────────┘
```

The copy column is vertically centered against the artifact, not aligned to its top. Left
column gets: eyebrow, headline, body, and then either a thin metric line or a row of pill
tags — one or the other, never both.

**Split headlines must fit two lines — five or six short words.** This is a hard constraint,
not a preference. The column is only ~620px wide, so a longer headline wraps to three lines and
the accent phrase breaks across a line break; the first accented word then renders at the pale
end of the gradient and reads as plain white, which silently destroys the emphasis. If the
headline will not fit, either shorten it or move the slide to the statement archetype, where
the headline has the full width. Split headlines are set at 62px rather than the 76px used on
statement slides for the same reason.

Artifacts can bleed past the right margin. It suggests the product is larger than the frame
and is one of the few places to break the grid deliberately.

## 4. Diagram

Full-width architecture. External systems as chips around the perimeter, the product as a
container in the middle, dashed connectors showing direction, a legend strip at the bottom.

Headline sits top-left as usual, but smaller — Headline M rather than L, because the diagram
is the message.

Rules that keep it readable:

- **Chips outside, product inside.** The visual boundary must be unmistakable; it is the
  entire point of an architecture slide.
- **Direction must be visible.** Arrowheads, or a legend explaining that lines are
  bidirectional. A diagram of undirected lines communicates almost nothing.
- **Highlight exactly one interior component** — the hard one.
- **Cap the chips at about eight**, then add a `+ 150 more` chip. Enumerating forty
  integrations makes the slide unreadable and reads as insecurity; a count is stronger.

## 5. Ranked rows

Three to five stacked rows, each: label and sublabel left, proportional bar centre, micro
stats and a large number right. Top row highlighted.

Bars must be proportional to a real quantity, and the quantity should be stated. A bar chart
whose lengths are decorative is the fastest way to lose a numerate reader — and every investor
is a numerate reader.

Order by the narrative, not always by size. For market slides, ordering by customer segment
from beachhead to enterprise tells a sequencing story that ordering by revenue would hide.

## 6. Metric trio

Three giant gradient numbers in one bordered container, separated by 1px dividers. Each has
the number, a mono label beneath, and one line of context.

Three is the maximum. Four reads as a dashboard, and a dashboard invites the reader to hunt
for the weak number instead of hearing the story.

Date-stamp the slide in the top-right area beneath the page counter — `AS OF APRIL 2026`.
Undated metrics are assumed stale, and the assumption is usually right.

## 7. Profiles

Two or three cards side by side: circular photo, name, role in accent mono, bio, then a row of
pill tags for credentials.

Optionally a full-width strip beneath holding a timeline — shared history, milestones, prior
ventures. On a team slide this strip does disproportionate work, because it addresses founder
risk without having to claim anything.

Photos: circular, consistent crop, consistent lighting. Mismatched headshots undermine a
polished deck more than almost anything else on a per-pixel basis.

## 8. Closing

Centered logo, one-sentence vision at Headline XL, URL beneath. Accent on the final clause.
Same construction as the cover, which bookends the deck.

Resist adding contact details, a QR code, or "thank you". The vision line is the last thing
the reader should be holding, and anything else on the slide competes with it. Contact
belongs in the bottom chrome.

## Choosing between them

When a slide's content does not obviously fit:

- Argument with no mechanism → **statement**
- One capability to explain → **split**
- Many parts and their relationships → **diagram**
- Ordered comparison → **ranked rows**
- Two or three numbers → **metric trio**
- People → **profiles**

If it fits none of them, the slide is probably doing two jobs. Split it, or cut it. Building a
ninth layout should happen roughly never, and when it does, it should be because the deck needs
that layout more than once.
