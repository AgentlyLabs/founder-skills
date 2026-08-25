---
name: wireframe
description: Turn a product idea, PRD, or existing codebase into a complete, buildable wireframe package - a screen inventory, low-fi HTML wireframes, a machine-readable screens.json contract, and a spec doc that a coding agent can build from 1:1. Use whenever someone asks to wireframe an app, mock up screens, plan a UI before building, produce a design spec for an AI to implement, or turn a feature request into screens. Also use before writing UI code for a feature that spans more than one screen.
---

# Wireframe

Produce a wireframe package that a coding agent can implement without asking a
single follow-up question.

The failure mode this skill exists to prevent: pretty mockups that look decided
but leave every real question open — what happens when the list is empty, where
does this button go, what is the validation message, what is this number called
in the database. A coding agent handed that will invent answers, and invent
different answers on every run. So the artifact of record here is **not** the
picture. It is `screens.json`, a contract. The HTML is a render of the contract
so a human can look at it and object.

## Non-negotiables

1. **`screens.json` is the source of truth.** Write it before any HTML. Every
   HTML element that matters carries `data-id` equal to its node id in the JSON.
   If they disagree, the JSON is right and the HTML is a bug.
2. **Closed component vocabulary.** Use only the primitives in
   `references/component-vocabulary.md`. Never invent one. Consistency across
   screens comes from the vocabulary being small, not from taste.
3. **Greyscale.** One accent color, used only on the single primary action per
   screen. A wireframe that looks like a visual design gets treated as one, and
   then nobody revisits the layout.
4. **Four states per screen.** default, empty, loading, error. Each is either
   rendered or explicitly marked `n/a` with a one-line reason. No silent gaps.
5. **Real copy, never lorem.** Button labels, headings, validation messages,
   and empty-state text are product decisions. Decide them here.
6. **Consistent fixtures.** The same fake people, orgs, and numbers appear on
   every screen. `Dana Whitfield` on screen 3 is the same `Dana Whitfield` on
   screen 7, with the same id.
7. **Validate before handoff.** `python3 scripts/validate.py <outdir>` must exit 0.

## Pipeline

Run these in order. Do not skip ahead to drawing — the expensive mistakes are
all made in phase 1, and they are free to fix there.

### Phase 0 — Brief

Establish, in this order of preference: read it, infer it, ask it.

- **Existing codebase?** Read routes, models/schema, and any existing UI before
  asking the user anything. Route files and DB schema give you the screen list
  and the data nouns for free.
- **PRD or issue?** Read it and extract the same.
- **Nothing but an idea?** Ask at most 5 questions, batched in one message:
  primary user and the one job they hire this app for; platform (responsive web
  / mobile / desktop); auth model (none / single user / teams+roles); the 3-6
  core data nouns; anything explicitly out of scope for v1.

Write `brief.md`. Keep it under a page. Include a **Non-goals** section — it is
the highest-leverage section in the package, because it is the one that stops a
coding agent from building things nobody asked for.

### Phase 1 — Inventory (stop and confirm here)

Write `inventory.md`:

- **Entities** — each data noun, its fields, and which screens touch it.
- **Screens** — a table of `id | route | purpose (one line) | entry points`.
  Screen ids are kebab-case and stable forever; they are used as filenames, as
  JSON keys, and as action targets.
- **Flows** — each primary flow as an ordered list of screen ids with the action
  that advances each step. Cover at minimum: first run, the core job, and the
  one destructive action (delete / cancel / leave).

Then **stop and show the user the screen list and flows.** Ask them to cut
screens. Do not start rendering until they respond. A wrong screen list produces
a whole package of consistent, well-validated, wrong wireframes.

### Phase 2 — Contract

Write `screens.json` per `references/screens-schema.md`. For every screen:
regions, components drawn from the vocabulary, data bindings back to entity
fields, all four states, every action with a resolvable target, and acceptance
criteria written as observable assertions ("submitting with an empty title shows
the inline error `Title is required` and does not navigate").

This is the phase that takes the longest and the phase that pays. Fill it in
completely — an unfilled field here becomes an invented decision downstream.

### Phase 3 — Wireframes

Copy `assets/wireframe.css` into the output directory once. Render each screen
from the JSON into `screens/<screen-id>.html` using
`assets/screen-template.html`. Every component gets `data-id`. Every state that
is rendered gets its own file: `screens/<screen-id>.empty.html`, etc.

Render from the JSON mechanically. If you find yourself adding something to the
HTML that is not in the JSON, that is a signal the JSON is incomplete — go back
and add it there first.

### Phase 4 — Spec

Write `spec.md` per `references/spec-format.md`. It is the human-readable
narrative over the same facts: flows, states matrix, copy deck, validation
rules, permissions, edge cases, open questions. It restates the JSON on purpose
— reviewers read prose, agents read JSON, and they must not drift.

### Phase 5 — Validate

```bash
python3 scripts/validate.py design/wireframes
```

It checks that every HTML `data-id` exists in the JSON and vice versa, that
every action target resolves to a real screen, that every screen declares four
states, that every component is in the vocabulary, that no screen is orphaned
(unreachable from any flow), and that no lorem or `TODO` survived. Fix every
finding. Re-run until it exits 0, then paste the output for the user.

### Phase 6 — Handoff

Write `index.html` (all screens on one scrollable board, grouped by flow) and
`BUILD.md` — the instructions for the coding agent that picks this up:

- read `screens.json` first, then `spec.md`; treat the HTML as reference only
- build screens in flow order, not file order
- component ids map to component names in the target codebase
- do not add screens, fields, or actions that are not in the contract; if one
  seems necessary, stop and report it as a gap

## Output layout

```
design/wireframes/
  brief.md
  inventory.md
  screens.json          <- the contract
  spec.md
  BUILD.md
  index.html
  wireframe.css
  screens/
    <screen-id>.html
    <screen-id>.empty.html
    <screen-id>.loading.html
    <screen-id>.error.html
```

## Regenerating

Wireframes get revised more often than they get created. On a change request:
edit `screens.json`, re-render only the affected screens, re-run the validator.
Never hand-edit an HTML file and leave the JSON behind — that is how the package
starts lying, and a lying contract is worse than no contract.

## References

- `references/component-vocabulary.md` — the closed primitive set, with the
  markup for each. Read before phase 3.
- `references/screens-schema.md` — `screens.json` schema and a worked example.
  Read before phase 2.
- `references/spec-format.md` — `spec.md` section template. Read before phase 4.
