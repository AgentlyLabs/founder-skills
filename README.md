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
skills/seo-audit/
├── SKILL.md
├── references/
│   ├── gsc-api-surface.md
│   ├── analyses.md
│   ├── onpage-checks.md
│   └── report-template.md
└── scripts/
    └── analyze_gsc.py
```

## Contributing

Issues and PRs welcome — particularly corrections. If a skill states something about an API
or a system that's wrong or out of date, that's the most valuable kind of bug report here,
since the whole point is that these are grounded in what the underlying tools actually do.

## License

MIT — see [LICENSE](LICENSE).
