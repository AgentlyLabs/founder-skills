# Sequences: follow-ups, timing, and volume

## The rule that governs the whole sequence

**Every follow-up must carry information the previous email did not.** A message whose only
content is that time has passed asks for attention while offering nothing, which is why
"just bumping this" underperforms sending nothing at all — it spends the remaining goodwill
and teaches the recipient that your emails are safe to ignore.

This constrains sequence length honestly. If you can only think of two things worth saying,
the sequence is two emails long.

## Shape

Three to four touches total. Each has a distinct job:

**Email 1 — the trigger.** Covered in `copy.md`. Under 125 words.

**Email 2 (+3 business days) — the proof.** One concrete artifact: a number from a
comparable customer, a short before/after, a link to the specific doc page that answers
the obvious objection. Shorter than email 1. Reply in the same thread.

**Email 3 (+4 business days) — the reframe.** Assume the first angle was wrong rather than
that the recipient was inattentive. A different entry point, a different stakeholder's
problem, or an explicit "I may have aimed this at the wrong thing." New thread, new subject.

**Email 4 (+5 business days) — the close.** State that you are stopping, and leave the door
open without a hook. "I'll stop here — if the warehouse thing resurfaces, reply to this and
I'll pick it up." This performs well for a real reason: it removes the pressure that was
suppressing the reply, and it is the last honest moment in the sequence.

Then stop. A fifth email converts a prospect into a complaint, and complaint rate is the
metric providers act on (see `deliverability.md`).

## Timing

- **3 to 5 business days** between touches. Tighter reads as pressure; looser loses the
  thread entirely.
- **Skip weekends and holidays.** A Saturday send is filed with the weekend backlog.
- **Send-time optimization is largely folklore.** The published "best time to send"
  research is almost all scored on open rate, which is not measurable. Send during the
  recipient's business hours in their timezone and stop optimizing a variable you cannot
  observe.
- **Total sequence span: two to three weeks.** Longer, and the trigger is stale — which
  matters, because the trigger was the entire justification for the email.

## Threading

Emails 2 and 3 reply in the original thread. This keeps the context visible and makes the
sequence read as one person following up rather than a system firing.

Start a new thread when the angle genuinely changes, since a new subject line gets a fresh
evaluation. Never fake a thread — no `Re:` on a message that is not a reply, and no
"following up on our conversation" where there was no conversation.

## Stop rules

Stop immediately and suppress permanently on:

- Any opt-out request, however informally phrased. "Not interested" is an opt-out.
- A hard bounce. Never retry a hard bounce; it is a direct reputation cost.
- An explicit "no."
- Any reply that routes you to someone else — the sequence ends and a new, referenced
  email begins.

Pause, do not stop, on an out-of-office: resume after the return date, and do not count
the auto-reply as engagement.

Suppression is permanent and applies across every campaign, not just the current one. This
is a legal requirement in the US and Canada and a GDPR obligation in the EU
(`compliance.md`), and it is also the only thing that keeps complaint rate survivable.

## Volume arithmetic

Work the numbers before building the list, because they set what the program can be:

- Reputation-safe cold volume is in the **low tens of emails per mailbox per day**, well
  under provider caps. Provider limits are an abuse ceiling, not a plan.
- A 4-touch sequence means each new prospect generates ~4 sends over three weeks, so
  steady-state daily volume is roughly `new prospects/day × 4`.
- **The 0.30% spam-complaint ceiling is 3 complaints per 1,000 sends.** At 50 sends a day,
  a single complaint every three weeks puts you at the threshold. This is the constraint
  that makes untargeted volume self-defeating rather than merely rude.
- Reply rate falls as list size grows, because the specific reason for the email is what
  earns the reply and it does not survive scale. A 40-prospect list with real triggers
  routinely beats a 4,000-prospect list, and costs less domain reputation.

## Tracking and CRM hygiene

- **Do not use open tracking.** It is not measurable (`deliverability.md`), a tracking
  pixel is a bulk-mail signal, and it will produce confidently wrong decisions.
- **If you use click tracking, use a custom tracking domain.** Shared ones get blocklisted
  by association.
- **Log the trigger with the contact.** The reason you emailed someone is the most valuable
  field in the record, and the one that lets you write a good email again in six months.
- **Record the opt-out date and source.** Required to demonstrate compliance, and required
  to avoid re-import from a stale list re-starting the whole problem.
