# `screens.json` schema

The contract. Everything else in the package is derived from this file or
validated against it.

## Top level

```jsonc
{
  "meta":     { … },   // product identity + defaults
  "entities": { … },   // the data nouns and their fields
  "fixtures": { … },   // the sample rows used on every screen
  "flows":    [ … ],   // ordered paths through the screens
  "screens":  [ … ]    // the screens themselves
}
```

### `meta`

| key | required | notes |
|---|---|---|
| `product` | yes | Product name as it appears in the UI |
| `version` | yes | Bump on every regeneration |
| `device` | yes | `desktop` \| `mobile` — the default for screens that omit it |
| `platform` | yes | `web` \| `ios` \| `android` \| `desktop-app` |
| `auth` | yes | `none` \| `single-user` \| `accounts` \| `teams` |
| `nonGoals` | yes | Array of strings. What v1 deliberately does not do |

### `entities`

```jsonc
"invoice": {
  "label": "Invoice",
  "fields": [
    { "name": "id",       "type": "uuid",     "required": true },
    { "name": "number",   "type": "string",   "required": true, "notes": "INV-0001, sequential per org" },
    { "name": "status",   "type": "enum",     "required": true, "values": ["draft","sent","paid","overdue"] },
    { "name": "total",    "type": "currency", "required": true },
    { "name": "dueDate",  "type": "date",     "required": false }
  ]
}
```

`type` is one of `uuid string text int currency date datetime bool enum email ref[<entity>] file url`.
Anything a screen displays must exist here — if a screen shows "days overdue"
and no field produces it, either add the field or document it as derived in
`notes`. A displayed value with no source is the most expensive kind of gap: the
coding agent will invent a computation, and it will be wrong.

### `fixtures`

Two to five rows per entity, reused on every screen. Names, numbers, and dates
must be internally consistent — if `inv-2` is `overdue` in the fixture, it is
overdue everywhere it appears, and its due date is in the past relative to the
other fixtures.

```jsonc
"invoice": [
  { "id": "inv-1", "number": "INV-0041", "status": "paid",    "total": 2400,  "dueDate": "2026-07-01" },
  { "id": "inv-2", "number": "INV-0042", "status": "overdue", "total": 18600, "dueDate": "2026-07-15" }
]
```

### `flows`

```jsonc
{
  "id": "send-first-invoice",
  "label": "Send the first invoice",
  "primary": true,
  "steps": [
    { "screen": "invoices",        "action": "invoices.btn-new",     "to": "invoice-new" },
    { "screen": "invoice-new",     "action": "invoice-new.form.submit", "to": "invoice-detail" },
    { "screen": "invoice-detail",  "action": "invoice-detail.btn-send",  "to": "invoice-detail.modal-send" }
  ]
}
```

Every screen must appear in at least one flow. The validator flags orphans,
because an unreachable screen is either dead scope or a missing entry point,
and both are worth knowing before anyone writes code.

Cover at minimum: first run / empty account, the core job end to end, and the
destructive path.

### `screens`

```jsonc
{
  "id": "invoices",
  "route": "/invoices",
  "title": "Invoices",
  "purpose": "Scan every invoice and find the ones that need chasing.",
  "device": "desktop",
  "entryPoints": ["nav-top", "dashboard.stat-overdue"],
  "regions": [
    { "id": "invoices.nav",  "role": "nav",    "components": [ … ] },
    { "id": "invoices.main", "role": "main",   "components": [ … ] }
  ],
  "states": { … },
  "acceptance": [ … ]
}
```

`role` is one of `nav | header | main | aside | footer`. Exactly one `main`.

### Components

```jsonc
{
  "id": "invoices.table",
  "type": "table",
  "props": {
    "columns": [
      { "label": "Invoice", "binds": "invoice.number", "align": "left",  "sorts": true },
      { "label": "Status",  "binds": "invoice.status", "align": "left",  "sorts": true },
      { "label": "Total",   "binds": "invoice.total",  "align": "right", "sorts": true },
      { "label": "Due",     "binds": "invoice.dueDate","align": "right", "sorts": true }
    ],
    "rowCount": 3,
    "sortDefault": "dueDate asc",
    "rowAction": { "do": "navigate", "target": "invoice-detail" }
  },
  "children": []
}
```

| key | required | notes |
|---|---|---|
| `id` | yes | `<screen-id>.<name>`, kebab-case, globally unique, stable |
| `type` | yes | Exactly a heading from `component-vocabulary.md` |
| `props` | yes | Per-primitive; see the vocabulary |
| `binds` | when it shows data | `<entity>.<field>` |
| `action` | on every interactive element | see below |
| `children` | for containers | array of components |

### Actions

```jsonc
"action": { "on": "click", "do": "navigate", "target": "invoice-detail" }
```

`do` is one of:

| `do` | `target` means |
|---|---|
| `navigate` | a screen id |
| `open` | a screen id ending in `.modal-*` |
| `submit` | the form's own id; pair with `onSuccess` and `onError` |
| `back` | — |
| `none` | — (and say why in `props.note`) |
| `external` | `external:<what>`, e.g. `external:stripe-checkout` |

Every target must resolve. This single rule is what makes the package clickable,
and clickable is what makes a reviewer catch the missing screen.

### States

All four keys are required on every screen.

```jsonc
"states": {
  "default": { "render": true,  "file": "screens/invoices.html" },
  "empty":   { "render": true,  "file": "screens/invoices.empty.html",
               "trigger": "org has zero invoices",
               "copy": { "title": "No invoices yet",
                         "body": "Create your first invoice to start getting paid.",
                         "action": "New invoice" } },
  "loading": { "render": true,  "file": "screens/invoices.loading.html",
               "variant": "skeleton" },
  "error":   { "render": true,  "file": "screens/invoices.error.html",
               "trigger": "list request fails",
               "copy": { "title": "Couldn't load invoices",
                         "body": "Check your connection and try again.",
                         "action": "Retry" } }
}
```

To skip one: `{ "render": false, "reason": "modal is opened with data already in memory" }`.
`reason` is required when `render` is false. The validator rejects a bare
`false` — the point is not to force four files, it is to force four decisions.

### Acceptance criteria

Observable assertions, one per line, in the vocabulary of the screen. These are
what a coding agent checks its own work against, so write them as things that
are either visibly true or visibly false:

```jsonc
"acceptance": [
  "Rows are sorted by due date ascending on first load.",
  "An overdue invoice shows its due date with the danger treatment; no other row does.",
  "Clicking any row navigates to invoice-detail for that invoice.",
  "With zero invoices the table is replaced by the empty state, and the New invoice button remains visible.",
  "The search field filters on invoice number and client name only."
]
```

Avoid criteria that are not observable from the UI ("the query is efficient"),
and avoid restating the layout ("there is a table") — the JSON already says that.
