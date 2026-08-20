# Copy: what earns a reply

This is the least verifiable part of outbound, so the rules below are stated with their
mechanism. Where the common advice is folklore, it is labeled as such.

## The anatomy

Five parts, in order, no exceptions:

1. **Subject** — 2 to 5 words, lowercase or sentence case, no promise.
2. **The trigger** — **one** sentence, about them, falsifiable.
3. **The bridge** — **one** sentence connecting the trigger to what you do. A number and a
   mechanism.
4. **The ask** — one concrete thing, closed with a soft question.
5. **The sign-off** — your name, and the opt-out line.

**Target 50 to 80 words. Treat 125 as a hard ceiling, not a goal.** The reason is
mechanical rather than aesthetic: on a phone, roughly the first 100 words are visible
without scrolling, and an ask below the fold is an ask that requires a decision to reach.

The most common failure in a *good* draft is a second sentence per section — the one that
explains the inference you just drew. Cut it. Stating "that ordering is unusual, and it
usually means X" is you theorizing at someone who already knows their own situation. Give
them the observation and let them draw the conclusion; that is what makes them reply.

## Subject lines

The subject has one job: earn the open without spending the trust you need for the reply.
Two schools do this, by opposite mechanisms. Both work. Most guidance only teaches the
first, which is why so much competent cold email is also forgettable.

### School one — the specific reference

Look like internal mail from someone who had a reason to write. The mechanism is
recognition: the recipient sees their own world in the subject line and reads it as
colleague mail rather than campaign mail.

`your Postgres job posting` · `question about the migration` · `terraform + 4 engineers`

Low variance, low ceiling. Nearly impossible to get wrong, and rarely remarkable.

### School two — the pattern interrupt

Say something so unlike the surrounding inbox that curiosity does the work. The mechanism
is a gap: the subject withholds enough that opening is the cheapest way to resolve it.

`unsolicited SQL` · `dead models` · `wrong person?` · `bad news about your changelog`

High variance, high ceiling. And it carries one hard condition:

> **The body must pay off the interrupt in the first sentence.** An interrupt the email does
> not honor is a bait-and-switch, and the recipient learns it in three seconds — you spent
> trust to buy an open, which is exactly backwards.

The strongest interrupts are the ones that are *literally true*. `unsolicited SQL` works
because the email is unsolicited and it does contain a query — it names the awkward thing
about itself before the reader can, which is disarming rather than clever. Pair that subject
with an email whose ask is a concrete give and the subject is an accurate description of the
message. Pair it with a request for a 30-minute call and it is a lie that also insults the
reader.

The general form: **find the true, slightly uncomfortable summary of your own email and put
that in the subject.** It cannot be replicated by a template, which is exactly why it
survives an inbox full of them.

The same test kills the tempting ones: `wrong person?` is excellent if you genuinely are
unsure you have the right contact, and cheap manipulation if you know you do.

**Frame the payoff as what they get, not what you are offering.** The instinct is to write
"I'll trade you a 20-line query for a reply," which pays off the subject but spends the
best line in the email on the word *I*. Invert it:

> You get a 20-line SQL query. I get a reply, if it turns out useful.

Same trade, same disarming honesty, and the first word is now theirs. This is the one place
where school two and the first-sentence rule appear to conflict, and they do not — the
conflict is a symptom of writing the payoff from the sender's side.

### Which to use

An honest answer requires an honest caveat: **this skill cannot tell you which one wins.**
Subject-line A/B testing is scored on open rate, which is no longer measurable
(`deliverability.md`), so essentially every published claim about subject-line performance
rests on a broken instrument. Reply rate can settle it, but needs volume most targeted
programs do not have.

So this is judgment, labeled as judgment:

- **Use the specific reference** when the trigger is strong enough to carry the email by
  itself, when the recipient is senior enough that gimmick reads as disrespect, or in
  regulated and conservative industries.
- **Use the pattern interrupt** when your ask is a genuine give (the interrupt can then be
  literally true), when the recipient's inbox is saturated with competent-and-identical
  outreach, or when you have volume to learn from replies.
- **Never mix schools within a sequence.** Email 1 as an interrupt and email 2 as a
  reference reads as two different senders.

### Both schools fail the same way

- **Title case with a value proposition** — `Reduce Your Cloud Spend By 40%` reads as a
  campaign because it is written like one.
- **Fake threading** — a subject beginning `Re:` on a first contact. It gets a click and
  poisons the interaction at the first line of the body.
- **Personalization tokens in the subject** — `{{FirstName}}, quick question` announces the
  merge field even when it renders correctly.
- **Questions that invite "no"** — `Are you struggling with churn?`
- **Emoji** — in B2B cold, it marks the message as bulk.

Note that a pattern interrupt is not a licence for any of these. `🔥 Are You Struggling
With Churn?` is not school two; it is school one done badly with an emoji on it.

**Folklore to discard:** subject-line optimization to a specific character count. Published
ranges run from 2 to 8 words and disagree with each other because they are all scored on the
same broken instrument.

## The first sentence

The test is falsifiability: **could this sentence have been sent to 500 other people?** If
yes, it is not a first sentence.

Strong, because each references something checkable and specific:

- "You're hiring two data engineers whose job description is basically 'fix the warehouse
  before we can ship the analytics feature.'"
- "Your status page shows three incidents last month, all in the migration path."
- "Your docs say the SDK is Python-only, and your changelog says the Node client was
  planned for Q1."

Weak, and specifically recognizable as automation:

- "I hope this email finds you well." Says nothing, and appears in a large fraction of
  bulk mail, so it functions as a signal.
- "I loved your recent post!" — once a differentiator, now generated at scale, so it now
  reads as the opposite of what it intends.
- "As the VP of Engineering at Acme, you probably care about..." — visibly a merge of two
  fields plus an assumption.
- "Congrats on the funding!" with nothing following it. Reveals that the funding
  announcement was the only research done.
- Anything beginning "I'm reaching out because I..." — the first word is about you.

## The bridge

**One sentence.** This is where a number belongs if you have a real one, and where you must
not put one if you do not.

Two shapes work. Both describe the recipient's problem rather than your product:

- **Mechanism plus number.** "Usually that's dead models — scheduled refreshes on tables
  nobody queries. On a team your size that was most of a $41k to $23k a month cut."
- **Named consequence.** State what the problem costs if left alone. This is the strongest
  frame available *and* the easiest to get wrong, because the honest version describes a
  pattern you have observed, not a prophecy about their company.

  > "Most teams scaling this fast hit manual bottlenecks that delay shipping by weeks."

  This is the common template, and it fails the falsifiability test twice: "most teams" is
  unsourced and "by weeks" is invented. It also tells the recipient something about their
  own company that you cannot possibly know, which reads as presumption rather than
  insight. The fix is to narrow the claim until it is true:

  > "The teams we've seen do this end up rebuilding the same dedupe job three times."

  Specific, bounded to your own observation, and checkable against their experience — which
  is what makes them reply to correct you or agree.

- "We cut a similar team's warehouse spend from $40k to $23k a month, mostly by killing
  scheduled refreshes nobody read." — checkable shape, specific mechanism.
- "We help companies unlock 10x efficiency gains with AI-powered automation." — no
  mechanism, no referent, unfalsifiable. Reads as filler because it is.

Name a comparable company only if it is genuinely comparable and you have the right to
name it. An unrelated enterprise logo dropped into a startup pitch reads as a bluff.

## The ask

Two properties, and most drafts get only one of them:

- **Concrete** — the recipient knows exactly what "yes" produces.
- **Soft** — saying yes costs one word.

**One question mark per email.** Two questions do not double your chances; they split the
recipient's attention and make the reply feel like homework.

The standard advice stops at "soft," which is why so many polite cold emails go unanswered.
"Worth a look?" costs one word to accept but never says *a look at what*, so the recipient
has to invent the next step themselves — and inventing it is more work than ignoring you.
A calendar link has the opposite problem: perfectly concrete, and it asks for a 30-minute
decision from someone who has known you for eleven seconds.

**The shape that works: name one small thing you can send immediately, then close with two
words.**

> I can send the 20-line query we used to find the dead models. Want it?

Ranked, best first:

- **Concrete give + soft close.** "There's a two-paragraph writeup of how we did it. Send
  it over?" The give must be small, specific, and something you can actually attach to the
  next reply — a query, a checklist, a before/after, one number.
- **Diagnostic question with an honest exit.** "Already handled, or still on the list?"
  Works because a "yes, solved" reply is useful qualification rather than a failure. Weaker
  than a give, because it asks without offering.
- **Vague interest check.** "Worth a look?" Better than a calendar grab, worse than
  anything specific.
- **Meeting request.** "Open to 15 minutes Thursday?" Acceptable in a later email once
  there is a reason to meet. Weak in a first one.
- **Calendar link.** Asks the most, earns the least.

The give also solves the follow-up problem: if they say yes, email 2 writes itself and
arrives as something they asked for.

## Anti-patterns

Each of these is common, and each has a specific reason it fails:

| Pattern | Why it fails |
|---|---|
| "Just following up" / "circling back" / "bumping this" | Adds no information, so it asks for attention while giving none. |
| "Quick question" as the whole subject | So heavily used in bulk outbound that it now reads as a tell. |
| "I'll keep this brief" then 300 words | The claim is disproved on the same screen. |
| A booking link in email #1 | Maximum ask at minimum trust. |
| Attachments in a first email | A filtering liability and an unreasonable request. |
| Three or more links | Each one dilutes the single action and adds spam signal. |
| Fake urgency ("only this week") | Nothing about your calendar is urgent to a stranger. |
| Fake familiarity ("as we discussed") | An outright falsehood, and it is checkable. |
| Guilt escalation ("did you see my last email?") | Converts non-response into an accusation. |
| A signature block with six links, a logo, and a banner | Marks the message as marketing infrastructure. |
| Full-width HTML template | The single strongest bulk signal available. Send plain text. |

## Spam-trigger words: mostly obsolete

Word lists — "free," "guarantee," "act now" — descend from filters of the early 2000s.
Modern filtering weights authentication, domain and IP reputation, and engagement history
far above lexical content, which is why an authenticated message from a warm domain
containing "free trial" lands, and an unauthenticated message with impeccable vocabulary
does not.

What remains true: certain phrases correlate with filtering because of the *mail they
usually appear in*, not because a keyword rule fires. Pressure language, financial claims,
ALL CAPS, and excessive exclamation marks travel with bulk mail, so they are worth removing
— as evidence of an underlying problem, not as a checkbox.

`scripts/score_email.py` flags these as low-weight and says so. Do not let a user rewrite
around a word list while their DMARC is broken.

## Where the standard advice is wrong

Most published cold-email guidance agrees with this file on the important things: short,
mobile-first, lowercase conversational subject, verifiable trigger, recipient's problem not
your features, interest-based CTA, plain text, warmed secondary domain, lean signature.
Three points recur widely and do not survive contact with the primary sources.

**1. "Strip legal disclaimers from your signature."** Correct about corporate disclaimer
blocks, badges, and social icons. Wrong if applied to the opt-out line and the postal
address, which **CAN-SPAM and CASL require in every commercial message**
(`compliance.md`). Deleting them for deliverability's sake trades a style preference for a
statutory violation carrying per-message penalties.

The resolution is formatting, not omission: two plain-text lines that read like a sentence.

```
Prefer not to hear from me again? Say so and I'll close the file.
Agently Labs, 2261 Market St #5150, San Francisco, CA 94114
```

That satisfies both regimes and looks nothing like a marketing footer.

**2. "The majority of replies come from follow-ups."** This statistic circulates without
attribution, and where it is sourced it traces to email-sequencing vendors reporting on
their own customers — a population that by definition sends sequences, measured by the
company selling sequence software. It may well be directionally right. It is not
independent evidence, and it should not be quoted as a finding. Follow up because each
touch carries new information (`sequences.md`), not because of that number.

**3. "Space follow-ups 2–3 days apart."** Defensible, but note that most such timing advice
— including "best time to send" research generally — is scored on **open rate**, which is
no longer measurable (`deliverability.md`). Any cadence recommendation derived from open-rate
testing is measuring proxy fetches. 3–5 business days is this skill's default because it
leaves the trigger fresh while not reading as pressure, which is a judgment call rather than
a measured optimum, and it is labeled as one.

**On subject length**, published ranges run from 2 to 8 words. The linter warns above 6 and
fails above 8. Anywhere in that band is fine; the word count was never the variable that
mattered, and it cannot be A/B tested on opens.

## Formatting

- **Plain text.** No HTML template, no images, no tracking pixel. A 1:1 email should look
  like a 1:1 email at the protocol level as well as in the prose.
- **Short lines and blank lines.** Three or four short paragraphs, one idea each.
- **No bold, no bullets** in a first email. Formatting is a document convention, and this
  is a message.
- **A two-line signature.** Name, and one thing that establishes who you are. Then the
  opt-out and postal address, which `compliance.md` requires.

## Rewriting someone else's draft

Do these in order:

1. Cut the first sentence if it is about the sender. Almost always an improvement.
2. Find the trigger. If there is none, stop and say so — that is the real finding, and no
   amount of editing substitutes for it.
3. Delete every sentence that would survive being sent to a different company.
4. Delete every sentence that explains what the previous sentence implies.
5. Reduce to one question.
6. Replace the calendar link with a concrete give plus a two-word close. If you cannot name
   something small you could send them tomorrow, you do not yet have an ask.
7. Cut to 50–80 words, which usually means deleting the paragraph explaining the product.
8. Read it aloud. Anything you would not say out loud to a stranger comes out.
