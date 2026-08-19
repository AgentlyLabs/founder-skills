# Design system

Every value here is measured from a shipped deck, not invented. The canvas is **1600×900**,
rendered at 2× to **3200×1800**. Author at 1× and let the renderer scale — that way one set
of numbers describes both.

All of it is encoded in `assets/deck.css` as custom properties. Change the variables, not the
rules.

**The palette below is the default, not the design.** The structure — geometry, type scale,
chrome, surfaces — is what makes the system work and stays fixed. Colors should come from the
company's own website whenever there is one; see
[Deriving a palette from a brand](#deriving-a-palette-from-a-brand) and
`scripts/extract_brand.py`. The defaults are the Agently palette, which is a real shipped
theme rather than filler, so a deck built on them looks finished.

## Contents

- [Palette](#palette)
- [The accent gradient](#the-accent-gradient)
- [Type](#type)
- [Geometry](#geometry)
- [Slide chrome](#slide-chrome)
- [Surfaces](#surfaces)
- [Deriving a palette from a brand](#deriving-a-palette-from-a-brand)

## Palette (default)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0e0d13` | Slide background |
| `--surface` | `#16161e` | Card and panel fill |
| `--surface-2` | `#151419` | Nested or recessed panel |
| `--border` | `#212025` | Hairline borders, 1px |
| `--ink` | `#fbfaf6` | Headlines |
| `--body` | `#c9c9d1` | Body copy |
| `--muted` | `#6e6b7a` | Chrome labels, mono micro-text |
| `--accent` | `#c6a4f2` | Solid accent, links, active states |
| `--accent-dim` | `#8b6fb0` | Accent at low emphasis |

Two details that carry more weight than they look like:

**The background is not black.** `#0e0d13` has a violet cast. Against true `#000` it reads as
warmer and more deliberate, and it gives the purple accents something to sit in rather than
float on. Pure black backgrounds are the fastest way to make a dark deck look like a default
template.

**The headline white is not `#fff`.** `#fbfaf6` is very slightly warm. At 76px on a dark
field, pure white vibrates and feels cheap; the warm white reads as printed ink. Nobody
consciously notices this and everybody feels it.

## The accent gradient

```css
--grad: linear-gradient(100deg, #f0dedc 0%, #dec4eb 45%, #c6a4f2 100%);
```

Cream → pink → lavender, running left to right at a slight upward angle. Applied to text via
`background-clip: text`.

**Where it goes:** the payload words of a headline, and giant metric numbers. Nowhere else.

The rule that makes it work: **the gradient lands on the words that carry the claim, and the
sentence still parses if you read only those words.** "The model isn't the moat. *Your stack
is.*" — the accent is the argument. Gradients applied to a random trailing phrase look
decorative and cheapen the whole system.

One gradient direction across the entire deck. Mixing angles is the single most common way a
code-built deck starts looking assembled rather than designed.

## Type

Two families, and the split between them is semantic, not aesthetic:

- **Sans** (`Inter`, `Helvetica Neue`, system) — human prose. Headlines, body, names.
- **Mono** (`SF Mono`, `ui-monospace`, `Menlo`) — machine output. Timestamps, IDs, counts,
  section labels, artifact internals.

Holding that line is a large part of why the deck reads as credible. Mono says *this came out
of a system*; sans says *a person wrote this*. When mono is used decoratively for human copy,
the signal is lost and everything looks like a developer's side project.

| Role | Size | Weight | Line height | Tracking |
|---|---|---|---|---|
| Chrome label | 11px | 500 | 1 | `0.22em` |
| Eyebrow | 12px | 500 | 1 | `0.2em` |
| Headline XL (cover, close) | 46px | 700 | 1.2 | `-0.02em` |
| Headline L (statement slides) | 76px | 800 | 1.18 | `-0.025em` |
| Headline M (dense slides) | 54px | 800 | 1.15 | `-0.02em` |
| Body | 23px | 400 | 1.45 | 0 |
| Body small | 19px | 400 | 1.5 | 0 |
| Metric | 90px | 800 | 1 | `-0.03em` |
| Artifact mono | 15px | 400 | 1.7 | `0.02em` |
| Micro label | 11px | 500 | 1.4 | `0.18em` |

Headlines are uppercase **never**. Chrome labels, eyebrows, and micro labels are uppercase
**always**. There is no in-between case in this system.

## Geometry

| Property | Value | As fraction |
|---|---|---|
| Canvas | 1600×900 | 16:9 |
| Side margin | 60px | 3.75% of width |
| Top chrome baseline | 58px | 6.4% of height |
| Bottom chrome baseline | 842px | 93.6% of height |
| Card radius | 14px | |
| Pill radius | 999px | |
| Border width | 1px | at 1×; renders as 2px at 2× |
| Split: copy column | 40% | left |
| Split: artifact column | 55% | right, 5% gutter |

**The vertical band is the thing to internalize.** Content sits in a band roughly from 25% to
70% of slide height. The top and bottom quarters are mostly empty, holding only chrome. That
generous emptiness is most of what separates this from a template — the instinct to fill the
frame is exactly the instinct to resist. When a slide feels too empty, the fix is stronger
copy, not more elements.

## Slide chrome

Present on every slide, identical position:

- **Top left** — section label, mono, uppercase, `--muted`. One or two words:
  `PROBLEM`, `MARKET`, `PILLAR 01 · THE BRAIN`.
- **Top right** — page counter, mono: `04 / 11`.
- **Bottom left / right** — on cover and closing slides only: domain and contact.

The chrome does real work. It tells the reader where they are in an argument, which lets them
relax and follow it. A deck without it feels like a stack of loose images.

Do not repeat the section label as the eyebrow on the same slide. Seen in the wild: a slide
labeled `MARKET` top-left with the eyebrow `MARKET · BOTTOM-UP` directly beneath the
headline. It reads as duplication. Either make the eyebrow add information
(`BOTTOM-UP · US ONLY`) or drop it.

## Surfaces

**Standard card** — `--surface` fill, 1px `--border`, 14px radius.

**Highlighted card** — for the one element that matters most on the slide:

```css
background: linear-gradient(160deg, rgba(198,164,242,0.14), rgba(198,164,242,0.04));
border-color: rgba(198,164,242,0.35);
box-shadow: 0 0 60px rgba(198,164,242,0.10);
```

Exactly one highlighted element per slide. Two competing glows and the eye goes nowhere.

**Pill tag** — 1px border, 999px radius, 11–13px text, `--muted`. Used for capability lists
and credentials. Six maximum per row; past that it reads as a word cloud.

**Progress bar** — 4px tall, 999px radius, `--border` track, `--grad` fill. Width encodes the
value, so it must be proportional to something real.

**Connector line** — 1px dashed `rgba(198,164,242,0.3)` with a small triangular arrowhead.
For architecture diagrams, drawn as absolutely positioned elements or inline SVG.

## Deriving a palette from a brand

The structure survives a palette swap; the specific purple does not matter. `extract_brand.py`
automates this, but the rules matter when checking or overriding its output.

**Everything derives from one accent hue.** Pick the brand's primary accent — the most
saturated color it uses for emphasis, not its text or background color — and generate the rest
in HSL from that hue `H`:

| Token | Derivation from accent hue `H` | Why |
|---|---|---|
| `--bg` | `hsl(H, 18%, 6%)` | Near-black carrying the accent's cast, never neutral grey |
| `--surface` | `hsl(H, 12%, 10%)` | Cards read as lit by the same light |
| `--surface-2` | `hsl(H, 10%, 8%)` | Recessed panels |
| `--border` | `hsl(H, 8%, 14%)` | Hairlines that disappear until needed |
| `--ink` | `hsl(H, 6%, 98%)` | Warm white, tinted toward the brand |
| `--body` | `hsl(H, 8%, 80%)` | |
| `--muted` | `hsl(H, 8%, 45%)` | |
| `--grad` stop 1 | `hsl(H, 25%, 90%)` | Light and desaturated |
| `--grad` stop 2 | `hsl(H, 45%, 84%)` | |
| `--grad` stop 3 | the accent itself | |

The two rules that carry the most weight:

**The background must be tinted, never neutral.** A blue-accented deck wants `#0d0e14`; a
green-accented deck wants `#0c110e`. Neutral `#111` under a colored accent is what makes a
dark deck look like an unstyled template.

**The gradient must run light-to-saturated.** Starting desaturated and ending at the accent is
what keeps gradient *text* legible — a gradient between two fully saturated colors turns
headline words to mud at any size below the metric scale. If a brand has two accents, use the
second as stop 2 only if it is lighter than the primary; otherwise interpolate.

**Fonts.** If the site uses a distinctive typeface and it is available (Google Fonts or a
webfont URL), adopt it for headlines and keep the mono for machine text. If it is a licensed
font you cannot fetch, stay on the default stack — a substituted lookalike at the wrong
weights damages the deck more than using a clean neutral grotesk.

**Leave the type scale and geometry alone** unless the brand font has very different metrics.
Those numbers are doing the design work, not the colors.

**Light decks.** Invert `--bg`/`--ink`, and drop gradient text to solid accent — gradient text
on white is thin and hard to read below the metric scale. Expect to raise body weight to 450
and darken `--muted` substantially; a straight inversion of a dark theme reads washed out.
