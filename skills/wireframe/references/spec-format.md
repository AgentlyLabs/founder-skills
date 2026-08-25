# `spec.md` format

The human-readable half of the package. Same facts as `screens.json`, arranged
for someone who is going to argue with them. Reviewers read prose and catch
product mistakes; agents read JSON and catch nothing. You need both.

Write it after the JSON, from the JSON. If writing a section reveals a decision
you never made, go back and make it in the JSON first.

---

## 1. What this is

Two sentences on the product and one on who it is for. Then the version and the
date. Then a link line: `screens.json` is the contract, this doc explains it,
`index.html` shows it.

## 2. Non-goals

Bulleted, blunt, and first — before anyone gets attached. Each line is something
a reasonable person would otherwise assume is in scope. "No multi-currency."
"No approval chains — one person sends, one person pays." This section is the
reason a coding agent stops instead of scaffolding.

## 3. Entities

The table from `screens.json`: entity, field, type, required, notes. Add a
sentence per entity on what it is in the world, not in the database.

Call out derived values explicitly — anything a screen displays that is computed
rather than stored, with the computation written out.

## 4. Screens

One subsection per screen, in flow order:

- **Purpose** — one line, the same one as the JSON.
- **Route** and **entry points**.
- **Layout** — the regions and what is in them, in reading order. Prose, not a
  component dump; the JSON has the dump.
- **Data** — which entity fields appear and where.
- **Actions** — a table of `control | what happens | where you land`.
- **States** — the four, with their triggers and their exact copy.
- **Acceptance** — the criteria list from the JSON, verbatim.

## 5. Flows

Each flow as a numbered walkthrough with the screen ids inline, including what
the user sees on the way and where they can leave. Then the flow's failure
branches — what happens if the payment declines, if the file is too large, if
they close the tab mid-form.

## 6. States matrix

One table: screens down the side, `default / empty / loading / error` across the
top, each cell either the trigger or the reason it does not apply. It reads as a
checklist, and gaps in it are visible from across the room.

## 7. Copy deck

Every string in the product, in one table: `key | screen | string`. Buttons,
headings, empty states, validation messages, toasts, confirmations. Pulled from
the JSON, so it cannot drift.

The reason this is its own section: copy written inline while drawing is copy
written by whoever was drawing. Copy in a table is copy someone will edit.

## 8. Validation and permissions

Per form: field, rule, exact error message, when it fires (on blur / on submit).
Per role, if the app has roles: what each role can see and do, and what they get
instead when they cannot — a hidden control, a disabled control, or an error.
Say which; "handle permissions" is not a decision.

## 9. Edge cases

The list you would otherwise discover in review. At minimum: the longest
plausible string in every text slot, zero and one and many for every collection,
the slowest request, the offline case, the double-submit, the stale-tab case,
and the destructive action taken by accident.

## 10. Open questions

Numbered, each with who can answer it and what you assumed in the meantime. An
open question with a stated assumption is safe to build against; an open
question without one is a stall.

---

Keep the whole thing under ~1500 words per five screens. A spec nobody finishes
reading is a spec that does not constrain anything.
