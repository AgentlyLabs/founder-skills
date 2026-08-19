# Product artifacts

The signature move of this system, and the hardest part to do well. An artifact is a
**plausible surface of the product**, drawn in HTML and CSS, sitting where a stock photo or
icon would go.

## Why they work

A reader has seen ten thousand gradient blobs and abstract network illustrations. They convey
nothing, and worse, they signal that the company had nothing concrete to show.

An artifact conveys specificity, and specificity is the cheapest credibility available. A log
line reading `09:14 open Slack · copy thread` proves you have watched someone do this job. A
knowledge graph with nodes labeled `Acme Corp`, `ticket-127`, and `churn risk` proves you know
what lives in your customers' data. Neither claim is *made* anywhere in the copy — the artifact
just demonstrates it, which is why it lands.

They also make a deck look expensive, because they cannot be bought. Anyone can license an
illustration; nobody can license a picture of *your* product's internals.

## The honesty line

**An artifact may show a real feature in an idealized state. It may not show a feature that
does not exist.**

Clean data, a run that succeeded, a graph without orphan nodes — all fine, that is a product
screenshot on a good day. A capability you have not built is not fine, and neither is a metric
you made up. Any number inside an artifact must be real or visibly labeled illustrative.
Investors do diligence, and a fabricated figure discovered inside a screenshot ends the
conversation and the relationship.

When you need a number and do not have one, use a structural placeholder that is obviously not
a claim — `—` or `···` — rather than an invented figure.

## The five types worth building

### 1. The log

Timestamped rows of mono text showing a sequence of actions. Best artifact for a **problem
slide**, because it makes tedium visible in a way prose cannot.

Structure: a header row with a context label left and a title right, then six or seven rows of
`timestamp · action`, then a footer row with the aggregate cost. The footer is where the
argument lands — `↻ REPEAT × 12 / DAY` and `8H / WEEK LOST` do more work than the rows above
them.

Accent-color a repeated word across rows — the tool being pasted into, the step being redone.
The eye catches the repetition before reading a single line, which is the entire point.

### 2. The graph

Nodes and edges, either as a centered panel with satellites around it or as a free network.
Best for anything about relationships, memory, or context.

Label nodes with **real-looking entity names**, never `Node A`. Mix types deliberately —
company names, ticket IDs, channel names, metric names — because the mixture is what
communicates that the graph spans systems. Put timestamps on a few edges to imply temporality.
Dashed lines for inferred relationships, solid for explicit ones, and say which is which.

### 3. The board

Columns with cards, each card carrying a title, a mono status line, a thin progress bar, and
optional pill tags. Best for anything about orchestration, workflow, or pipeline.

What makes it read as live rather than mocked: **different states across cards**. One at 18%,
one at 72%, one done and approved. A board where every card looks identical reads as a
wireframe. Add one curved connector between a card in one column and a card in another to show
a dependency.

### 4. The document stack

Two or three overlapping cards at slight rotations, each with a pill label, a title, and
skeleton text bars for body copy. Best for output, templates, or generated-artifact slides.

Skeleton bars rather than lorem ipsum: real-looking fake text invites reading, and the reader
then discovers it is nonsense. Bars are honestly abstract. Vary their widths to imply
paragraphs.

Rotate by no more than 2–3 degrees. More looks like a design flourish rather than a stack of
real documents.

### 5. The chip constellation

Third-party integration chips — small rounded rectangles with a brand mark and a name — arranged
around a container, with dashed connectors pointing inward. Used on architecture slides.

Use real logos, sized consistently at 16px, and keep the chips visually identical apart from
the mark. Cap at eight and add a counted overflow chip. Vertically stagger them slightly;
a perfect row reads as a logo wall, a staggered arc reads as a system.

## Construction rules

- **Dark on dark.** Artifacts sit at `--surface` on a `--bg` slide, 1px `--border`, 14px
  radius. They should feel embedded in the slide, not pasted onto it.
- **Mono for everything inside.** Artifact internals are machine output. The only sans text is
  a card title.
- **One glow maximum.** The hero element gets the accent tint and box-shadow; nothing else
  competes.
- **Hairlines, not heavy strokes.** 1px at authoring scale. At 2× render it lands at 2px, which
  is exactly right.
- **Never a full-height artifact.** Let it occupy the content band and leave the top and bottom
  quarters empty like every other slide.
- **Text must survive the render.** Artifact mono is 15px on a 1600px canvas — small. Check the
  rendered PNG at 100% and confirm it is readable, because this is the first thing that breaks.

## When not to build one

Statement slides. The thesis slide should have no artifact at all — the restraint is what
signals the idea is load-bearing. A deck where every slide has a visual is a deck with no
emphasis, and the reader stops distinguishing the important slides from the routine ones.
