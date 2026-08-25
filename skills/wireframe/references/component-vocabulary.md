# Component vocabulary

A closed set. If a screen seems to need something not on this list, it almost
always needs two things from this list composed, or the screen is doing too
much. Adding a primitive is a deliberate change to this file, not an
improvisation inside one screen.

Every primitive renders with `class="wf-<type>"` and carries `data-id`.
The `type` string in `screens.json` is exactly the name in the heading.

## Frame

### `shell`
The page frame. Exactly one per screen, wrapping everything.
`<div class="wf-shell" data-id="x.shell" data-device="desktop|mobile">`
`data-device` drives the frame width. Pick one per screen and stay with it.

### `header`
Page title row: title, optional subtitle, optional action slot on the right.
```html
<header class="wf-header" data-id="x.header">
  <div><h1>Invoices</h1><p class="wf-sub">32 open · 4 overdue</p></div>
  <div class="wf-slot"><!-- buttons --></div>
</header>
```

### `section`
A labeled region inside a screen. Use to group; never nest more than two deep.
`<section class="wf-section" data-id="x.sec-billing"><h2>Billing</h2>…</section>`

## Navigation

### `nav-top`
Horizontal bar: product mark, up to 5 destinations, account slot.
Mark the current destination `aria-current="page"`.

### `nav-side`
Vertical destination list. Use instead of `nav-top` when there are more than 5
destinations or the app is tool-shaped rather than content-shaped.

### `tabs`
Switches views *within* one screen. Never use tabs to move between screens —
that is `nav-top`. Each tab declares a `panel` id in the JSON.

### `breadcrumb`
Only on screens more than two levels deep. Last item is text, not a link.

## Content

### `text`
A block of prose. `variant: lead | body | caption`.

### `stat`
One number with a label and optional delta. Group 2-4 in a `stat-row`.
```html
<div class="wf-stat" data-id="x.stat-mrr">
  <span class="wf-stat-n">$12,480</span><span class="wf-stat-l">MRR</span>
  <span class="wf-stat-d">+4.2%</span>
</div>
```

### `list`
Vertical repeating rows. Each row: optional leading avatar/icon box, primary
text, secondary text, optional trailing meta and row action.
Declare `rowCount` in the JSON (use 3 for the default state) and bind each slot
to an entity field.

### `table`
Columnar data with a header row. Declare every column with its field binding,
alignment, and whether it sorts. If you have more than 7 columns, the screen
needs a detail view, not a wider table.

### `card-grid`
Repeating cards in a grid. Use over `list` only when there is a visual/media
element per item worth the space.

### `key-value`
Read-only detail pairs. The default rendering for a "view record" screen.

### `media`
Placeholder for image, video, map, or chart. `variant: image | chart | map`.
Renders as a crossed box with the variant label. Never draw a fake chart — a
plausible-looking chart invites review of numbers that do not exist.

### `avatar`
Person or org mark. Initials only.

## Input

### `form`
Wraps fields and a submit row. Declares `submitAction` and `validation` in JSON.
Every form has exactly one primary button.

### `field`
`variant: text | textarea | number | email | password | date | currency`.
Declares `label`, `placeholder`, `required`, `help`, `errorMessage`, and the
entity field it binds to. The error message is real copy, decided now.

### `select`
Single choice from a known set. List the actual options in the JSON.

### `choice`
`variant: checkbox | radio | toggle`. For toggles, state what the on and off
positions mean in words — "Notify me on reply" reads unambiguously, "Email"
does not.

### `search`
Text input that filters the adjacent `list` or `table`. Declares which
component id it filters and which fields it matches.

### `filter-bar`
Row of `select` / `choice` controls above a `list` or `table`, plus a clear
control. Declares the target component id.

### `upload`
Drop target. Declares accepted types, max size, and the error copy for both.

### `stepper`
Multi-step form progress. Declares the step labels and which step this screen
renders. Each step is its own screen id.

## Action

### `button`
`variant: primary | secondary | danger | ghost`. One primary per screen, and it
is the only element allowed to carry the accent color. Every button declares an
`action` with a target: a screen id, `submit`, `none`, or `external:<what>`.

### `link`
Inline navigation. Same action rules as `button`.

### `menu`
Overflow actions behind a `…` trigger. List every item and its action; a menu
with unlisted items is a gap in the contract.

## Feedback

### `banner`
Page-level message. `variant: info | success | warning | danger`. Declares
whether it is dismissible and what makes it appear.

### `inline-error`
Field-level validation message. Rendered in the `error` state file.

### `empty-state`
Icon box, one-line explanation of why it is empty, and the action that fixes it.
Every `list`, `table`, and `card-grid` must declare one. This is the single most
commonly skipped decision in wireframing and the one agents most often invent.

### `loading`
`variant: skeleton | spinner`. Skeleton for known layouts, spinner for unknown
duration. Rendered in the `loading` state file.

### `toast`
Transient confirmation. Declares the trigger action and the exact copy.

### `modal`
Overlay with title, body, and up to two actions. Modals are their own screen id
suffixed `.modal-<name>` so they get their own states and acceptance criteria.

### `confirm`
A `modal` whose primary action is `danger`. Declares what is being destroyed,
whether it is reversible, and the exact confirmation copy. Required for every
destructive action in the app.

## Structure

### `pagination`
`variant: pages | load-more | infinite`. Declares page size.

### `divider`
Horizontal rule between sections. Carries no data.
