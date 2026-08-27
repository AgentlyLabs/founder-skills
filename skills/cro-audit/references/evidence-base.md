# Evidence base

Read this before writing findings. It exists because most CRO advice is repeated vendor
marketing, and a report that leans on it is indefensible the moment someone technical
reads it.

## How to read effect sizes in this field

Nearly every dramatic number in published CRO content — "we increased conversions 137%" —
comes from a vendor case study. Three things are true of that literature:

- **Publication bias is close to total.** Nobody publishes the test that lost, and nobody
  publishes the 300 that did nothing. The visible distribution is the right tail only.
- **Most of it is underpowered.** A 137% lift on a few hundred visitors is a confidence
  interval wide enough to drive a truck through, reported as a point estimate.
- **Effect sizes shrink with maturity.** The teams running the most experiments report the
  smallest effects. At large mature products, a change producing a 1% relative improvement
  is a good quarter. Reported hit rates from teams that publish honestly cluster low —
  roughly a third of ideas positive at Microsoft, around one in ten at Booking.com, with
  the rest neutral or negative. Anyone promising you a 40% lift is selling something.

So: **use external effect sizes for direction, never for magnitude.** When a finding's
estimate rests on outside evidence rather than this account's data, say so in the report.
The four evidence classes to label with are *measured here*, *measured in this account*,
*established externally*, and *hypothesis*.

## Tier 1 — reliable mechanisms

These are worth reporting as findings on reasoning alone, because the mechanism is sound
and the failure mode is concrete. Direction is dependable; magnitude is not.

**Message match (information scent).**
A visitor arrives with an expectation set seconds earlier by an ad, an email subject
line, or a search result. If the page does not visibly restate that promise, the cheapest
action is to leave. This is the best-supported idea in the field and rests on real
research foundations (information foraging theory, Pirolli & Card) rather than case
studies. It is also the highest-leverage check on any paid landing page, and the one most
often skipped because it requires knowing the traffic source.

**Every field is a decision point.**
Form length affects completion. The direction replicates widely; the magnitude does not
and depends heavily on how motivated the visitor is and whether the field looks
justified. The commonly quoted "each field costs 10%" is folklore with no defensible
source — do not use it. Report field count as a measured fact and the *unjustified* field
count as the finding. Phone number on a content download is the canonical case: it does
not reduce completion because it is one more field, it reduces completion because it
announces a sales call.

**Unstated cost blocks the decision.**
B2B pages that hide pricing behind "book a demo" convert worse for self-serve-inclined
buyers, who now have to spend a meeting to learn a number. The mechanism is not
mysterious. This does not mean publish pricing — for genuinely enterprise sales it can be
wrong — but *unstated by default with no reasoning* is a finding worth surfacing.
Adjacent and cheaper: trial length, whether a card is required, and what happens at the
end of the trial. Those should never be a mystery.

**Speed, at the extremes.**
The relationship between latency and conversion is real and has been measured in
controlled server-side delay experiments at search scale, where hundreds of milliseconds
moved revenue per user by fractions of a percent. Two things follow. First, the effect is
genuine but modest at the margin — going from 1.9s to 1.6s is not where your conversion
problem lives. Second, the tail is what matters: a page that takes eight seconds on a
mid-range Android on 4G is losing people outright, and that is a different finding from a
Lighthouse score of 78.

Use **field data from real users** (CrUX) rather than a lab run. The often-cited Amazon
and Google latency figures are from 2006–2009 retail and search at enormous scale, and
are routinely misapplied to a B2B SaaS page with 3,000 monthly visitors.

**Mobile input configuration.**
Wrong `type`, missing `inputmode`, missing `autocomplete`, tap targets under ~44px. These
are not preference questions — they are defects. They make a form measurably harder to
complete on the device where most of the traffic is. Almost always broken, almost never
tested, and correctly shipped without an experiment.

**Trust placed at the moment of commitment.**
Proximity matters more than presence. A security badge in the footer and a security badge
beside the submit button are not the same intervention. The same is true of the refund
policy, the "no credit card required" line, and the privacy assurance next to an email
field. Measure the DOM distance between the primary control and the nearest trust
element.

## Tier 2 — contingent

Real mechanisms, but the sign of the effect depends on context. Propose these as
experiments where the traffic supports it, and as reasoned judgment calls where it does
not. Never assert them as universally correct.

- **Social proof.** Specific beats voluminous — a named customer with a role and a
  concrete outcome outperforms a wall of anonymous five-star quotes. But proof of the
  wrong audience actively hurts: enterprise logos on a page selling to solo developers
  signal "not for you, and expensive."
- **Page length.** "Shorter converts better" is not a law. Long pages win for
  considered purchases where the visitor genuinely has questions; short pages win where
  intent is already high. What reliably loses is length made of filler.
- **Video on the hero.** Can raise or lower conversion. Autoplay with sound reliably
  lowers it.
- **Urgency and scarcity.** Effective when true, corrosive when manufactured. A countdown
  that resets on reload is a trust liability, and increasingly a regulatory one — the FTC
  and EU consumer rules both treat fabricated scarcity as a dark pattern.
- **Number of pricing tiers, and anchoring.** Real effects, highly product-specific.
- **Single-column vs multi-step forms.** Multi-step can improve completion via commitment
  and reduced perceived effort, or hurt it by hiding total length. Depends on the ask.
- **Live chat.** Helps considered purchases, annoys self-serve.

## Tier 3 — folklore. Do not report these as findings.

Including any of these is how the whole report gets dismissed.

- **Button color.** The famous red-beats-green results were tests of contrast and
  prominence within one specific page, generalized into a law they never supported. Color
  has no context-free effect. Contrast against surroundings does, and that is what to
  measure.
- **"Above the fold" as a universal law.** Users scroll, and have for two decades. What
  matters is whether the first screen makes the case for scrolling. A CTA below the fold
  on a considered-purchase page is not automatically a defect.
- **Fixed numbers of "principles."** Thirteen principles, twenty-seven hacks. If the list
  is the same for every site, it was not derived from any site.
- **"Reduce clicks."** Click count is not the cost function; uncertainty and effort per
  step are. A three-step form with obvious progress beats a one-page form with thirty
  fields.
- **Exit-intent popups as a default good.** They reliably capture some emails and
  reliably cost some goodwill. Not a finding; a tradeoff with a business decision behind
  it.
- **Generic urgency, fake counters, and "only 3 left" on infinite digital goods.**
- **Heatmap aesthetics.** Heatmaps are a hypothesis generator, not evidence. "The heatmap
  shows people don't scroll" is an artifact of how the tool aggregates, not a measurement
  of intent.
- **Any claim sourced to "studies show" with no study.** Including in this document — if a
  claim here has no mechanism stated, treat it as tier 2.

## A note on where to spend the audit

At low traffic the highest-value findings are almost always tier 1 defects: broken mobile
inputs, a form asking for things it does not need, a headline that does not match the ad,
a price nobody can find. They are cheap, they are correct without testing, and they are
usually all present at once.

Tier 2 is where experimentation belongs, and experimentation requires volume the site may
not have. Do not spend the report proposing tier 2 tests to a site with 400 visitors a
week. See `experiment-design.md`.
