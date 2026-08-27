# Founder Skills

Open-source [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) that automate
the work of running a startup — the functions a founder is forced to own personally before
there is anyone to hire for them. One new skill daily.

A founder does fundraising, outbound, growth, hiring, and finance in the same week, mostly
badly, mostly because there is no time to get good at five jobs at once. Each skill here
takes one of those jobs and makes it something you delegate rather than learn.

Every skill is built the same way: grounded in primary sources rather than folklore,
explicit about what the underlying data can and cannot support, and shipped with the
reference material and scripts it actually needs — not just a prompt.

## Skills

| Function | Skill | What it does |
|---|---|---|
| Fundraising | [`pitch-deck`](skills/pitch-deck) | Investor-grade decks built as HTML and rendered to a 16:9 PDF. A dark editorial design system whose palette is derived from your own website, an eleven-slide narrative arc, and "product artifact" visuals instead of stock imagery. |
| Sales | [`cold-email`](skills/cold-email) | Cold outbound that reaches an inbox and earns a reply. Audits your sending domain's SPF/DKIM/DMARC against the actual Google and Yahoo bulk-sender rules, applies the consent regime for the recipient's jurisdiction (CAN-SPAM, GDPR/ePrivacy, CASL), and lints the draft against reply rate — not open rate, which is no longer measurable. |
| Growth | [`seo-audit`](skills/seo-audit) | Full SEO audit from Google Search Console data via MCP — striking-distance queries, CTR gaps measured against the site's own position curve, cannibalization detection, and traffic-decay diagnosis, output as a prioritized report with the impact arithmetic shown. |
| Conversion | [`cro-audit`](skills/cro-audit) | Landing page and funnel audit where every finding cites a measurement taken from the actual page — form and input defects, message match against the ad that paid for the click, trust placement, rendered fold and occlusion — and a validator blocks any claim not traceable to one. Sizes every proposed A/B test against real traffic first, and says plainly when the site cannot run one. |
| Product | [`wireframe`](skills/wireframe) | Wireframes an app end to end into a package a coding agent can build 1:1. A `screens.json` contract is the artifact of record, low-fi HTML screens are rendered from it, and a validator blocks the handoff until every state, action, binding, and user-facing string has actually been decided — the decisions a mockup leaves open and a model silently invents. |

"End-to-end" is the goal, not a claim about today. Five functions are covered. Hiring,
finance, support, and product analytics are not yet, and this table is the honest scoreboard.

## Install

### Claude Code

Clone into your personal skills directory to make every skill available in every project:

```bash
git clone https://github.com/AgentlyLabs/founder-skills.git /tmp/founder-skills && mkdir -p ~/.claude/skills && cp -r /tmp/founder-skills/skills/* ~/.claude/skills/
```

Or copy a single skill into one project, so it ships with the repo and your team gets it:

```bash
mkdir -p .claude/skills && cp -r /tmp/founder-skills/skills/cold-email .claude/skills/
```

### Claude Desktop and claude.ai

Skills upload one at a time, as a zip. Build them all with:

```bash
git clone https://github.com/AgentlyLabs/founder-skills.git && cd founder-skills && ./scripts/package.sh
```

That writes `dist/pitch-deck.zip`, `dist/cold-email.zip`, `dist/seo-audit.zip`,
`dist/wireframe.zip` and `dist/cro-audit.zip`. Then, in Claude:

1. Open **Settings → Capabilities** and turn on **Code execution and file creation**.
   That toggle is what gates Skills — without it the Skills menu doesn't appear. On Team
   and Enterprise an owner enables it for the org under **Settings → Skills** instead.
2. Go to **Customize → Skills**, click **+**, choose **Upload skill**, and pick a zip.
3. Repeat for each skill, then toggle the ones you want on.

The archive has to contain the skill *folder* — `SKILL.md` sits one level down, never at
the root of the zip. `package.sh` gets this right; zipping from inside a skill directory
is the most common reason an upload is rejected.

Uploads are per-account. They aren't shared with your organization, and they don't sync
to Claude Code — each surface is installed separately.

### What runs where

Claude Code runs a skill on your machine, with your network and your binaries. Claude
Desktop and claude.ai run it in a sandbox, which changes what some of the scripts can do:

| Skill | Claude Code | Claude Desktop / claude.ai |
|---|---|---|
| [`wireframe`](skills/wireframe) | Full | Full — `validate.py` is pure stdlib |
| [`cold-email`](skills/cold-email) | Full | Copy linting works; the domain audit needs `dig`, which the sandbox doesn't have |
| [`pitch-deck`](skills/pitch-deck) | Full | The HTML deck builds; the 16:9 PDF render shells out to Chrome and won't |
| [`seo-audit`](skills/seo-audit) | Full | Needs a Search Console connector — see below |
| [`cro-audit`](skills/cro-audit) | Full | Partial — `ab.py` and `verify.py` are pure stdlib and run anywhere; `measure.py` needs outbound HTTP and the rendered checks need browser control, so neither works in the sandbox |

Nothing here is broken on Desktop. The parts that reach outside the sandbox are the parts
that don't run, and each skill says so rather than guessing at the answer it can't measure.
If you want the live domain audit or the rendered PDF, use Claude Code.

### Connecting Search Console for `seo-audit`

`seo-audit` doesn't scrape anything or estimate rankings from the outside. It reads your
own Google Search Console data through an MCP connector, so one has to be connected
before it can pull.

There is no single canonical GSC MCP server, and the skill deliberately doesn't hardcode
tool names — it discovers whatever you have connected and maps it onto the Search Console
API surface documented in
[`references/gsc-api-surface.md`](skills/seo-audit/references/gsc-api-surface.md).

**Claude Desktop** — **Settings → Connectors → Add custom connector**, paste the server
URL, then authorize it against the Google account that owns the property. For a server
that runs locally rather than over HTTP, install it as a desktop extension under
**Settings → Extensions**.

**Claude Code** — add it from the terminal:

```bash
claude mcp add search-console -- <your-gsc-server-command>
```

Either way, confirm the connection can actually see your property before running an audit.
Property type matters: a domain property (`sc-domain:example.com`) aggregates every
subdomain and protocol, a URL-prefix property (`https://example.com/`) does not. Auditing
the second and reporting it as whole-site truth is the most common invisible error in an
SEO audit.

With no connector at all, the skill tells you and offers a best-practice-only audit from
crawling the live site, clearly labeled as having no performance data behind it. It won't
quietly degrade into a generic checklist.

---

Claude picks a skill up automatically when a request matches its description — you don't
need to invoke it by name. "Why is nobody replying to my outreach" reaches for
`cold-email` on its own.

## How these are built

Skills are structured for progressive disclosure: `SKILL.md` holds the workflow and stays
small, `references/` holds the detail that only gets read when it's needed, and `scripts/`
holds the deterministic work that shouldn't be re-derived by a model on every run.

```
skills/cold-email/
├── SKILL.md
├── references/
│   ├── deliverability.md
│   ├── compliance.md
│   ├── copy.md
│   └── sequences.md
├── assets/
│   └── example-emails.md
└── scripts/
    ├── check_domain.py
    └── score_email.py
```

The scripts matter more than they look. A model asked to reason about SPF lookup limits or
DMARC alignment will produce something plausible most of the time; `check_domain.py`
resolves the actual records and is right every time. Anything a founder would act on
should be measured, not recalled.

## Contributing

Issues and PRs welcome — particularly corrections. If a skill states something about an API
or a system that's wrong or out of date, that's the most valuable kind of bug report here,
since the whole point is that these are grounded in what the underlying tools actually do.

## License

MIT — see [LICENSE](LICENSE).
