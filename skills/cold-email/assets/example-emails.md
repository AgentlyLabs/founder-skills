# Worked examples

Both drafts below are scored by `scripts/score_email.py`. The first is the shape almost
everyone actually sends; the second is the same pitch after the rewrite order in
`references/copy.md`.

## Before — scores 0/100, 18 FAIL

```
Subject: Quick Question About Your Data Infrastructure

Hi Sarah,

I hope this email finds you well! I'm reaching out because I came across your
profile and as the VP of Engineering at Northwind, you probably care about data
quality.

At Agently we're a cutting-edge AI-powered platform that helps world-class
engineering teams leverage automation to unlock 10x efficiency gains across their
entire data stack. We guarantee results. Our seamless integration means you can
be up and running in minutes with ZERO engineering lift, and we've helped
companies like Google and Microsoft move the needle on their most critical
initiatives.

Would you be open to a quick 15 minute call this week to discuss how we could
help Northwind? Do you have time Thursday? I'd love to pick your brain about
your current setup.

Here's my calendar: https://calendly.com/agently/30min
You can also check out our site at https://agently.dev and read our case study
at https://agently.dev/case-studies/acme

Looking forward to hearing from you!

Best regards,
Ahmad
```

What is wrong with it, in the order that matters:

1. **No trigger.** Nothing here required Sarah to exist. "I came across your profile" and
   "as the VP of Engineering at Northwind" are two merge fields and an assumption. This is
   the finding no rewrite can fix — it has to be researched.
2. **165 words**, so the ask is below the fold on a phone.
3. **Two questions**, which splits the reply into homework.
4. **Three links, one of them a calendar** — maximum ask at minimum trust.
5. **Unfalsifiable claim stack**: cutting-edge, AI-powered, world-class, leverage, 10x,
   seamless, guarantee, move the needle. No mechanism and no referent anywhere.
6. **Google and Microsoft as logos** in a pitch to a mid-size company reads as a bluff.
7. **No opt-out and no postal address** — a CAN-SPAM violation, not merely bad style.

## After — every copy check clean, 76/100

```
Subject: unsolicited SQL

Hi Sarah,

You get a 20-line SQL query. I get a reply, if it turns out useful.

Both of Northwind's data engineer postings put "reduce warehouse cost" above
building new pipelines. Usually that's dead models — scheduled refreshes on
tables nobody queries. The query finds them; on a team your size that was most
of a $41k to $23k a month Snowflake cut.

Want it?

Ahmad, CTO @ Agently
```

What changed, and why:

- **The subject is a pattern interrupt that is literally true.** `unsolicited SQL` earns the
  open on curiosity, and the email is in fact unsolicited and does contain a query — so
  nothing is spent to get the open. It names the awkward thing about itself before Sarah
  can, which is disarming rather than clever. The same subject over a request for a
  30-minute call would be a lie.
- **The interrupt is paid off in the first line, framed as what she gets.** "You get a
  20-line SQL query. I get a reply" resolves the subject immediately and still opens on
  her. Writing it as "I'll trade you a query for a reply" pays off the same subject while
  spending the best line in the email on the word *I*.
- **The trigger is checkable.** Two named job postings and the order of the bullets inside
  them. Sarah can verify it, which is what makes it read as a person rather than a system.
- **No sentence explains its own inference.** An earlier draft added "that ordering is
  unusual, and it usually means the bill outgrew the team." Cut — she knows why she wrote
  the posting, and narrating it back is the sender talking.
- **The diagnosis is her problem, not the product.** "Dead models — scheduled refreshes on
  tables nobody queries" names a specific, recognizable failure. The company and what it
  sells are never mentioned.
- **The number is attached to a mechanism.** "$41k to $23k by killing dead models" is
  falsifiable. "Reduce warehouse costs by up to 40%" is not.
- **The ask is concrete and the close is soft.** A 20-line query is small, specific, and
  deliverable in the next reply. "Want it?" costs one word, and she knows exactly what yes
  produces — which "worth a look?" never tells her.
- **68 words, zero links, reading grade 5.2.** Ask visible without scrolling, nothing to
  click, longest sentence 17 words.
- **A two-word signature.** Name and role. No logo, no social icons, no disclaimer block —
  each of those is a bulk signal.

### Why this scores 76 and not 100

Every copy and formatting check passes. The two remaining FAILs are both legal:

```
FAIL   Opt-out (CAN-SPAM)         No opt-out mechanism.
FAIL   Postal address (CAN-SPAM)  No physical postal address.
```

This is the most useful thing the linter does, because it is the tradeoff nobody makes
consciously. A sales cold email is a "commercial electronic mail message" under CAN-SPAM,
and there is no exemption for 1:1 sending — the postal address and working opt-out are
required in every one (`references/compliance.md`). Enforcement against low-volume targeted
outreach is rare, which is why the overwhelming majority of cold email omits both. That is
a risk decision, not a style decision, and the point of the check is that you make it
knowingly rather than by default.

Restoring compliance costs two lines and does not have to read like a footer:

```
Prefer not to hear from me again? Say so and I'll close the file.
Agently Labs, 2261 Market St #5150, San Francisco, CA 94114
```

Add those and the same email scores 100.

And note the linter's standing caveat either way: a lint score says nothing about the
trigger. This email earns a reply *because* a human read the job postings first. The same
structure wrapped around a fabricated observation would score identically and deserve
nothing.

## The sequence

Following `references/sequences.md` — each touch carries new information.

**Email 2, +3 business days, same thread.** New information, and the give escalates rather
than repeats:

```
Worth adding: the dead models were only about 60% of it. The rest was two
dashboards nobody had moved off hourly refresh.

The query finds both. Still happy to send it over.
```

**Email 3, +4 business days, new thread, `Subject: wrong angle?`:**

```
I may have aimed this at the wrong thing. If the cost line is already owned,
the other pattern in postings like yours is that nobody can say which
dashboards are load-bearing before a migration.

Is that closer?
```

**Email 4, +5 business days, the close:**

```
I'll stop here. If the warehouse cost question comes back around, reply to this
and I'll pick it up.
```

Then stop, and suppress. A fifth email converts a prospect into a spam complaint, and at
these volumes three complaints per thousand sends is the entire budget
(`references/deliverability.md`).
