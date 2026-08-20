# Agently Skills

Open-source [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) for Claude Code.
One new skill released daily.

Every skill here is built the same way: grounded in primary sources rather than folklore,
explicit about what the underlying data can and cannot support, and shipped with the
reference material and scripts it actually needs — not just a prompt.

## Skills

| Skill | What it does |
|---|---|
| [`seo-audit`](skills/seo-audit) | Full SEO audit from Google Search Console data via MCP — striking-distance queries, CTR gaps measured against the site's own position curve, cannibalization detection, and traffic-decay diagnosis, output as a prioritized report with the impact arithmetic shown. |
| [`pitch-deck`](skills/pitch-deck) | Investor-grade pitch decks built as HTML and rendered to a 16:9 PDF. A dark editorial design system whose palette is derived from your own website, an eleven-slide narrative arc, and "product artifact" visuals instead of stock imagery. |
| [`cold-email`](skills/cold-email) | Cold outbound that reaches an inbox and earns a reply. Audits the sending domain's SPF/DKIM/DMARC against the actual Google and Yahoo bulk-sender rules, applies the consent regime for the recipient's jurisdiction (CAN-SPAM, GDPR/ePrivacy, CASL), and lints the draft against reply rate — not the open rate, which is no longer measurable. |

## Install

Clone into your personal skills directory to make a skill available in every project:

```bash
git clone https://github.com/AgentlyLabs/skills.git /tmp/agently-skills && mkdir -p ~/.claude/skills && cp -r /tmp/agently-skills/skills/* ~/.claude/skills/
```

Or copy a single skill into one project, so it ships with the repo and your team gets it:

```bash
mkdir -p .claude/skills && cp -r /tmp/agently-skills/skills/seo-audit .claude/skills/
```

Claude picks a skill up automatically when a request matches its description — you don't
need to invoke it by name.

## How these are built

Skills are structured for progressive disclosure: `SKILL.md` holds the workflow and stays
small, `references/` holds the detail that only gets read when it's needed, and `scripts/`
holds the deterministic work that shouldn't be re-derived by a model on every run.

```
skills/pitch-deck/
├── SKILL.md
├── references/
│   ├── narrative.md
│   ├── design-system.md
│   ├── slide-archetypes.md
│   └── artifacts.md
├── assets/
│   ├── deck.css
│   └── example-deck.html
└── scripts/
    ├── build_deck.py
    └── extract_brand.py
```

## Contributing

Issues and PRs welcome — particularly corrections. If a skill states something about an API
or a system that's wrong or out of date, that's the most valuable kind of bug report here,
since the whole point is that these are grounded in what the underlying tools actually do.

## License

MIT — see [LICENSE](LICENSE).
