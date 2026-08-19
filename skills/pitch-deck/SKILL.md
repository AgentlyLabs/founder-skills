---
name: pitch-deck
description: Build investor-grade pitch decks as HTML rendered to a 16:9 PDF — a dark editorial design system, a narrative arc that earns each slide, and "product artifact" visuals (fabricated-but-plausible UI, logs, graphs, boards) instead of stock imagery or clip art. Use this whenever the user wants a pitch deck, investor deck, fundraising deck, seed or Series A deck, demo-day deck, or a board or partner presentation; asks to design, write, restructure, critique, or redesign slides; asks what slides their deck needs or what order they should go in; wants a specific slide built (problem, solution, market sizing, traction, team, vision, architecture); or wants an existing deck upgraded to look like it came from a design studio. Also use when the user wants slides built as code rather than in Keynote, PowerPoint, Figma, or Google Slides. Trigger even when they never say "pitch deck" — "I'm raising and need something to send investors", "make me slides for the Sequoia meeting", and "our deck looks amateur, fix it" are all this skill.
---

# Investor-Grade Pitch Decks

## What this skill actually does

It builds decks as **HTML rendered to PDF at 16:9**, using a dark editorial design system
and a discipline about narrative that matters more than the visuals.

Building slides as code is not a gimmick here. It buys three things Keynote cannot: a design
system enforced by CSS variables so nothing drifts slide to slide, product artifacts drawn
in real markup instead of screenshotted or faked in a vector tool, and version control on
the narrative. The output is a normal PDF that opens anywhere.

## The one rule that determines whether the deck works

**Never open a design tool before the narrative is settled.** A beautifully typeset deck
carrying a muddled argument is worse than an ugly one carrying a sharp argument, because the
polish invites the reader to look closely at reasoning that cannot survive it.

So the workflow is strictly: interrogate → outline → write headlines → then build. Read
`references/narrative.md` before writing a single slide. If the user hands you content and
asks only to "make it look good," still run the narrative check first and say plainly what
the argument is missing — then build what they asked for.

## Step 1 — Interrogate before designing

You need real answers to these. Ask directly; do not invent them, and do not proceed on
assumptions for the first four.

1. **Stage and ask.** Pre-seed, seed, Series A? Raising how much, for what runway? This sets
   what evidence is expected — a pre-seed deck can sell a thesis, a Series A deck cannot.
2. **The wedge.** Who is the first user, precisely, and what do they do the morning after
   they sign up?
3. **Why now.** What changed in the last 18 months that makes this possible and did not
   before? A deck with no credible "why now" reads as a company that could have been
   started at any point and therefore probably will not win.
4. **The evidence.** Actual numbers: users, revenue, retention, pipeline, waitlist. Whatever
   is real, however small.
5. **The uncomfortable question.** What will the sharpest person in the room push on? Decks
   that pre-empt their strongest objection outperform decks that hide it.
6. **Brand.** Ask for the **company website URL** — that is the fastest path to a deck that
   looks like it came from the same company as the product. See Step 1b. If there is no
   site yet, the defaults in `references/design-system.md` are production-ready as-is.

If the user cannot answer 2 or 3, that is the finding. Say so before building — it is more
useful than a deck that papers over the gap.

## Step 1b — Derive the palette from the company's website

A deck should look like the product it is selling. Given a URL, generate the theme instead of
picking colors by hand:

```bash
python3 scripts/extract_brand.py https://example.com --out brand.css
```

The script fetches the page and its stylesheets and pulls the brand signal in priority order:
`:root` CSS custom properties first (modern sites declare their palette there, and it is by
far the highest-signal source), then `<meta name="theme-color">`, then a frequency count of
every color literal in the CSS. It picks an accent, then derives a complete dark theme from
it — background, surfaces, borders, warm ink, and the three gradient stops — using the HSL
relationships documented in `references/design-system.md`. Output is a `:root` block that
drops straight into the deck, overriding the defaults.

**Then verify it by eye.** Open the site with your browser tools and compare. The script reads
CSS, so it cannot see a palette that lives in images, nor tell a brand accent from a warning
red that happens to appear often. Fix what looks wrong and say what you changed — a derived
palette is a starting point, not an answer.

If the site is light-themed, the script still derives a **dark** deck from its accent hue,
because this system is dark. That is usually right: a dark deck reads as more considered in a
room with a projector. When a brand is strongly light-identified, `references/design-system.md`
covers the light inversion.

With no URL and no brand, the default palette is Agently's, and it is a complete, tested
theme — not a placeholder to be replaced.

## Step 2 — Outline against the arc

`references/narrative.md` holds the eleven-slide arc, what each slide must accomplish, and
the failure mode each one usually falls into. Eleven is a deliberate target: enough to carry
an argument, short enough that every slide has to earn its place.

Write the **headline for every slide before building any of them**, as a flat list. Read them
in order, top to bottom. The headlines alone should tell the whole story — if they do, the
deck will work; if they don't, no amount of layout will save it. This takes ten minutes and
is the highest-leverage step in the entire process.

## Step 3 — Choose an archetype per slide

`references/slide-archetypes.md` documents eight layouts with the content shape each one
fits. Every slide should map to one of them. Inventing a ninth layout for a single slide is
almost always a sign the content belongs in one of the eight.

The most important is the **split**: copy on the left, product artifact on the right. It
carries the product slides, and the artifact is what makes the deck feel like it came from a
company that has actually built something.

## Step 4 — Build the artifacts, not illustrations

This is the signature move of the system and the thing most decks get wrong.
`references/artifacts.md` covers it in full.

The principle: rather than an icon or a stock photo, each product slide shows a **plausible
surface of the actual product** — a terminal log with timestamps, a knowledge graph with real
entity names, a kanban board mid-run, a document template with skeleton text. Drawn in HTML
and CSS, dark on dark, hairline borders.

These work because they are *specific*. A log line reading `09:14 open Slack · copy thread`
does something no icon can: it proves you understand the user's actual day. Generic
illustration proves nothing.

**The honesty line matters.** An artifact may depict a real feature in an idealized state —
clean data, a successful run. It may not depict a feature that does not exist, and metrics
inside artifacts must be real or visibly labeled as illustrative. Investors do diligence, and
a fabricated number found in a screenshot ends the conversation.

## Step 5 — Assemble and render

Copy `assets/deck.css` and build one HTML file with all slides. The CSS variables carry the
whole design system, so per-slide styling should be rare.

```bash
python3 scripts/build_deck.py deck.html --out deck.pdf
```

That produces a real multi-page 16:9 PDF with selectable text, using headless Chrome and no
other dependencies. Add `--png` to also export each slide as a 3200×1800 PNG for social
posts or embeds.

**Always read the rendered output before delivering it.** Headless rendering diverges from
what the markup implies — clipped headlines, a body column colliding with an artifact, a
gradient that lands on the wrong word. Open the PNGs, look at them, fix and re-render. Every
deck needs at least one round of this; assume the first render is wrong somewhere.

## Step 6 — Critique before shipping

Read the deck as a skeptical investor and check the things that actually sink decks:

- **Headline test.** Read only the headlines. Is there an argument, or a list of topics?
- **The 30-second test.** From slide 1 alone, is it clear what the company does? Positioning
  statements that could describe five companies are the most common failure.
- **Evidence density.** Every claim either has a number or is honestly framed as a belief.
- **The objection.** Is the strongest counter-argument addressed, or hidden?
- **Slide count.** Anything that does not advance the argument gets cut, not shrunk.
- **Consistency.** One gradient direction, one card radius, one margin. Drift reads as
  carelessness and undermines everything else.

## What this system deliberately omits

The eleven-slide arc has no competition matrix and no financial projections slide. That is a
choice suited to early-stage decks, where a five-year revenue model is fiction and a
competitor grid invites the reader to shop. For a Series A or later, both usually need to
exist — `references/narrative.md` covers how to add them without wrecking the pacing. Do not
silently omit them from a later-stage deck just because the default arc does.

## Reference files

- `references/narrative.md` — the arc, headline craft, copy rules. **Read first.**
- `references/design-system.md` — palette, type scale, spacing, chrome. Measured values.
- `references/slide-archetypes.md` — the eight layouts and when each applies.
- `references/artifacts.md` — building product-surface visuals in HTML/CSS.
- `assets/deck.css` — the design system as production CSS.
- `assets/example-deck.html` — three archetypes wired up, ready to render.
- `scripts/build_deck.py` — HTML → PDF (and optional PNG) via headless Chrome.
