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

"End-to-end" is the goal, not a claim about today. Three functions are covered. Hiring,
finance, support, and product analytics are not yet, and this table is the honest scoreboard.

## Install

Clone into your personal skills directory to make every skill available in every project:

```bash
git clone https://github.com/AgentlyLabs/founder-skills.git /tmp/founder-skills && mkdir -p ~/.claude/skills && cp -r /tmp/founder-skills/skills/* ~/.claude/skills/
```

Or copy a single skill into one project, so it ships with the repo and your team gets it:

```bash
mkdir -p .claude/skills && cp -r /tmp/founder-skills/skills/cold-email .claude/skills/
```

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
