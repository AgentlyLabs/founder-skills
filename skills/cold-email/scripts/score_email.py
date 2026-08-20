#!/usr/bin/env python3
"""Lint a cold email draft against the rules in references/copy.md and compliance.md.

Quotes the offending text rather than just naming a rule, so every finding is actionable.

    python3 score_email.py draft.txt
    python3 score_email.py draft.txt --jurisdiction ca
    python3 score_email.py draft.txt --json

The draft may begin with a `Subject:` line. Exit status is 1 if any check FAILs.

This is a lint pass, not a verdict. A trigger-less email can score 100 — the trigger is
judged by a human, not by this script.
"""

import argparse
import json
import re
import sys

# ── Phrase tables ───────────────────────────────────────────────────────────────
# Each entry: (regex, why it fails). Reasons come from references/copy.md.

ANTI_PATTERNS = [
    (r"hope (?:this|the) (?:email |message )?finds you well", "Says nothing, and appears in a large share of bulk mail — it functions as a signal."),
    (r"hope (?:you(?:'re| are)|all is) (?:doing )?well", "Filler opener. Costs a line and earns nothing."),
    (r"just (?:following up|checking in|circling back)", "Adds no information — asks for attention while giving none."),
    (r"\bcircl(?:e|ing) back\b", "Adds no information. Every follow-up must carry something new."),
    (r"bump(?:ing)? this", "Announces that the email has no new content."),
    (r"did you (?:see|get|receive) my (?:last |previous )?(?:email|message)", "Converts non-response into an accusation."),
    (r"as (?:we|previously) discussed", "Fake familiarity, and it is checkable."),
    (r"per my last email", "Reads as a reprimand."),
    (r"\bquick question\b", "So heavily used in bulk outbound that it is now a tell."),
    (r"i(?:'ll| will) (?:keep this|be) brief", "The claim is disproved on the same screen."),
    (r"i(?:'m| am)? ?reach(?:ing)? out", "The first word is about you."),
    (r"touch base", "Corporate filler with no concrete ask."),
    (r"pick(?:ing)? your brain", "Asks for unpaid time with no stated value."),
    (r"at your earliest convenience", "Formal padding that softens the ask into nothing."),
    (r"let me know your thoughts", "A non-ask. No specific question to answer."),
    (r"i (?:loved|enjoyed|came across|stumbled (?:up)?on)\b", "Generated at scale now, so it reads as the opposite of personal."),
    (r"congrats on the (?:funding|raise|round)", "Reveals that the announcement was the only research done."),
    (r"as the (?:VP|Head|Director|CTO|CEO|Chief)\b", "Visibly a merge of two fields plus an assumption."),
    (r"\b(?:synerg|game[- ]chang|revolutionar|world[- ]class|best[- ]in[- ]class|cutting[- ]edge|thought leader)", "Unfalsifiable claim language. No mechanism, no referent."),
    (r"\b(?:seamless(?:ly)?|effortless(?:ly)?|turnkey)\b", "Marketing adjective. Says nothing checkable."),
    (r"\b(?:leverage|utilize)\b", "Jargon for 'use'. Reads as a template."),
    (r"\b10x\b|\b(?:unlock|drive|supercharge)\s+(?:efficien|growth|value|ROI)", "Claim with no mechanism or number behind it."),
    (r"\bAI[- ]powered\b", "Category word, not a benefit. Every competitor says it."),
    (r"low[- ]hanging fruit|move the needle|boil the ocean", "Cliché that displaces a specific statement."),
]

# Descended from early-2000s filters. Modern filtering weights authentication, domain
# reputation and engagement far above lexical content — see references/deliverability.md.
SPAM_ADJACENT = [
    r"\bact now\b", r"\blimited time\b", r"\brisk[- ]free\b", r"\bno obligation\b",
    r"\bclick here\b", r"\bbuy now\b", r"\bspecial offer\b", r"\bwinner\b",
    r"\b100% (?:free|guaranteed)\b", r"\bguarantee(?:d)?\b", r"\bcash bonus\b",
    r"\bsave big\b", r"\burgent\b", r"\bexpires? (?:today|soon)\b",
]

CALENDAR_LINKS = [
    r"calendly\.com", r"\bcal\.com", r"savvycal\.com", r"chilipiper", r"hubspot\.com/meetings",
    r"meetings\.hubspot", r"book (?:a|some) time", r"grab (?:any|a) slot", r"my calendar",
    r"scheduling link",
]

OPT_OUT = [
    r"unsubscrib", r"opt[- ]out", r"\bopt out\b", r"reply (?:with )?[\"']?stop",
    r"(?:say so|let me know) and i(?:'ll| will) (?:stop|close|leave)",
    r"i(?:'ll| will) (?:stop|not email|leave you)", r"no more emails",
    r"close the file", r"won(?:'t| not) (?:email|write) again",
]

ADDRESS_HINTS = [
    r"\b\d+\s+[\w.'-]+\s+(?:st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive|way|ct|court|pl|place|sq|square|hwy|pkwy)\b",
    r"\b(?:suite|ste\.?|floor|fl\.?|unit|apt\.?)\s*#?\s*\d+",
    r"\bp\.?\s?o\.?\s+box\s+\d+",
    r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b",          # US state + ZIP
    r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s+\d[A-Z]{2}\b",  # UK postcode
    r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b",              # Canadian postal code
]

MERGE_TOKENS = [r"\{\{[^}]*\}\}", r"\[\[[^\]]*\]\]", r"\*\|[^|]*\|\*", r"%%[A-Za-z_]+%%",
                r"\[(?:FIRST_?NAME|COMPANY|TITLE|first_name|company)\]"]

YOU_WORDS = r"\b(?:you|your|yours|you're|youre|yourself)\b"
ME_WORDS = r"\b(?:i|i'm|im|i've|ive|i'll|my|me|we|we're|were|our|ours|us|myself)\b"

URL_RE = re.compile(r"https?://[^\s<>\"')]+|\bwww\.[^\s<>\"')]+", re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class Finding:
    def __init__(self, check, status, detail, quote=None, fix=None):
        self.check, self.status, self.detail = check, status, detail
        self.quote, self.fix = quote, fix

    def as_dict(self):
        return {"check": self.check, "status": self.status, "detail": self.detail,
                "quote": self.quote, "fix": self.fix}


# ── Parsing ─────────────────────────────────────────────────────────────────────

def parse_draft(text):
    subject, body = None, text
    lines = text.splitlines()
    for i, line in enumerate(lines[:3]):
        m = re.match(r"^\s*subject\s*:\s*(.+)$", line, re.I)
        if m:
            subject = m.group(1).strip()
            body = "\n".join(lines[:i] + lines[i + 1:])
            break
    return subject, body.strip()


def split_signature(body):
    """Split off signature and legal footer so they don't distort prose metrics.

    The compliance footer is required (see references/compliance.md) but it is not part
    of the pitch: its opt-out line is not a second "ask", and its "I'll close the file"
    is not the sender talking about themselves.
    """
    lines = body.splitlines()

    for i, line in enumerate(lines):
        if re.match(r"^\s*(?:--+|__+)\s*$", line):
            return "\n".join(lines[:i]).strip(), "\n".join(lines[i + 1:]).strip()
        if re.match(r"^\s*(?:thanks|best|cheers|regards|best regards|sincerely|"
                    r"all the best|talk soon)[,.!]?\s*$", line, re.I):
            return "\n".join(lines[:i]).strip(), "\n".join(lines[i:]).strip()

    # No explicit delimiter: peel trailing legal/identity lines from the end. Only commit
    # to the split if an opt-out or postal address was actually seen down there.
    peel_from, saw_legal, i = None, False, len(lines) - 1
    while i >= 0:
        line = lines[i]
        if not line.strip():
            i -= 1
            continue
        if find_all(OPT_OUT, line) or find_all(ADDRESS_HINTS, line):
            saw_legal, peel_from = True, i
        elif "?" not in line and len(line.split()) <= 8:
            peel_from = i          # name, company, or bare URL line
        else:
            break
        i -= 1

    if saw_legal and peel_from is not None:
        return "\n".join(lines[:peel_from]).strip(), "\n".join(lines[peel_from:]).strip()
    return body, ""


def syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
    word = re.sub(r"^y", "", word)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", word)))


def readability(prose):
    sents = [s for s in SENTENCE_SPLIT.split(prose) if s.strip()]
    words = re.findall(r"[A-Za-z']+", prose)
    if not sents or not words:
        return None, 0, 0
    syl = sum(syllables(w) for w in words)
    grade = 0.39 * (len(words) / len(sents)) + 11.8 * (syl / len(words)) - 15.59
    return round(grade, 1), len(words), len(sents)


def find_all(patterns, text):
    hits = []
    for pat in patterns:
        entry = pat if isinstance(pat, tuple) else (pat, None)
        for m in re.finditer(entry[0], text, re.I):
            hits.append((m.group(0), entry[1], m.start()))
    return hits


def quote_context(text, pos, span, width=64):
    start = max(0, pos - 18)
    end = min(len(text), pos + span + 18)
    frag = " ".join(text[start:end].split())
    return ("…" if start else "") + frag[:width] + ("…" if end < len(text) else "")


# ── Checks ──────────────────────────────────────────────────────────────────────

def check_subject(subject):
    out = []
    if not subject:
        out.append(Finding("Subject", "WARN", "No Subject: line in the draft.",
                           fix="Add one. 2–5 words, sentence case, no promise."))
        return out

    words = subject.split()
    if len(words) > 8:
        out.append(Finding("Subject", "FAIL", f"{len(words)} words — too long.", subject,
                           "Cut to 2–6 words. Long subjects read as campaigns."))
    elif len(words) > 6:
        out.append(Finding("Subject", "WARN", f"{len(words)} words.", subject,
                           "Aim for 2–6 words."))
    else:
        out.append(Finding("Subject", "PASS", f"{len(words)} words.", subject))

    if re.match(r"^\s*re\s*:", subject, re.I):
        out.append(Finding("Subject", "FAIL", "Fake threading with 'Re:' on a first contact.",
                           subject, "Remove 'Re:'. It buys a click and poisons the first line."))

    content = [w for w in words if len(w) > 3]
    if content and sum(1 for w in content if w[0].isupper()) >= max(2, len(content) - 1) \
            and not subject.isupper():
        out.append(Finding("Subject", "WARN", "Title Case reads as a marketing campaign.",
                           subject, "Use sentence case or lowercase."))

    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", subject):
        out.append(Finding("Subject", "FAIL", "Emoji in subject marks the message as bulk.",
                           subject, "Remove it."))

    if re.search(r"\d+%|\bfree\b|\bguarantee", subject, re.I):
        out.append(Finding("Subject", "WARN", "Subject carries a value-prop claim.", subject,
                           "Subjects that promise read as campaigns. Reference something of theirs."))
    return out


def check_first_sentence(prose):
    sents = [s.strip() for s in SENTENCE_SPLIT.split(prose) if s.strip()]
    if not sents:
        return [Finding("First sentence", "FAIL", "Body is empty.")]
    first = sents[0]
    out = []

    if re.match(r"^\s*(?:hi|hey|hello|dear)\b[^,\n]*[,.]?\s*$", first, re.I) and len(sents) > 1:
        first = sents[1]
    else:
        first = re.sub(r"^\s*(?:hi|hey|hello|dear)\b[^,\n]*,\s*", "", first, flags=re.I)

    if re.match(r"^\s*(?:i|i'm|im|i've|my|we|we're|our|let me)\b", first, re.I):
        out.append(Finding("First sentence", "FAIL", "Opens with the sender, not the recipient.",
                           first[:90], "Lead with something about them. Cut this sentence — "
                                       "removing it is almost always an improvement."))
    else:
        out.append(Finding("First sentence", "PASS", "Opens on the recipient.", first[:90]))

    # Falsifiability proxy: a specific reference usually carries a number, a capitalised
    # term mid-sentence, or a quoted phrase.
    specifics = (re.findall(r"\b\d[\d,.]*\b", first)
                 + re.findall(r"(?<!^)(?<![.!?]\s)\b[A-Z][A-Za-z0-9]{2,}\b", first)
                 + re.findall(r"[\"'][^\"']{4,}[\"']", first))
    if not specifics:
        out.append(Finding("First sentence", "WARN", "No specific, checkable detail.",
                           first[:90], "Could this be sent to 500 other people? If yes, it is "
                                       "not a first sentence. Name the posting, the changelog "
                                       "entry, the number."))
    return out


def check_length(prose):
    words = re.findall(r"[A-Za-z0-9']+", prose)
    n = len(words)
    if n > 125:
        return [Finding("Length", "FAIL", f"{n} words — over the 125-word ceiling.",
                        fix="Target 50–80. The ask must be visible on a phone without "
                            "scrolling; usually the paragraph explaining the product is the "
                            "one to delete, followed by any sentence that explains what the "
                            "previous sentence implies.")]
    if n > 90:
        return [Finding("Length", "WARN", f"{n} words.",
                        fix="Under the 125 ceiling but above the 50–80 target. Look for "
                            "sentences that explain your own inference.")]
    if n < 25:
        return [Finding("Length", "WARN", f"{n} words — thin.",
                        fix="Too short to carry a trigger and a bridge.")]
    return [Finding("Length", "PASS", f"{n} words.")]


def check_ask(prose):
    out = []
    qs = re.findall(r"[^.!?\n]*\?", prose)
    qs = [q.strip() for q in qs if q.strip()]
    if len(qs) == 0:
        out.append(Finding("The ask", "FAIL", "No question — nothing to reply to.",
                           fix="Add one low-commitment question. 'Worth a look?' works."))
    elif len(qs) == 1:
        out.append(Finding("The ask", "PASS", "Exactly one question.", qs[0][:80]))
    else:
        out.append(Finding("The ask", "FAIL", f"{len(qs)} questions.",
                           " / ".join(q[:40] for q in qs[:3]),
                           "Cut to one. Two questions split attention and make the reply "
                           "feel like homework."))

    cal = find_all(CALENDAR_LINKS, prose)
    if cal:
        out.append(Finding("The ask", "WARN", "Calendar grab in a first touch.",
                           quote_context(prose, cal[0][2], len(cal[0][0])),
                           "Maximum ask at minimum trust. Replace with an interest check "
                           "('worth a look?') and send the link after they reply."))
    return out


def check_links(prose):
    urls = URL_RE.findall(prose)
    out = []
    if len(urls) > 2:
        out.append(Finding("Links", "FAIL", f"{len(urls)} links.", ", ".join(urls[:3]),
                           "One maximum. Each extra link dilutes the single action and adds "
                           "spam signal."))
    elif len(urls) == 2:
        out.append(Finding("Links", "WARN", "2 links.", ", ".join(urls),
                           "Cut to one."))
    else:
        out.append(Finding("Links", "PASS", f"{len(urls)} link(s)."))

    if re.search(r"\b(?:attach(?:ed|ing)|see the deck|find enclosed|PDF attached)\b", prose, re.I):
        out.append(Finding("Links", "WARN", "References an attachment.",
                           fix="No attachments in a first email — a filtering liability and an "
                               "unreasonable request."))
    return out


def check_balance(prose, subject=None):
    text = f"{subject or ''}\n{prose}"
    you = len(re.findall(YOU_WORDS, text, re.I))
    me = len(re.findall(ME_WORDS, text, re.I))
    detail = f"you/your: {you}, I/we: {me}"

    # Below a handful of first-person references the ratio is noise, not a signal — an
    # email can address the recipient by company name and never say "you".
    if me < 4:
        return [Finding("Focus", "PASS", detail + " — too few to rate, and that is fine")]

    ratio = round(you / me, 2)
    detail += f" (ratio {ratio})"
    if ratio < 0.6:
        return [Finding("Focus", "FAIL", detail,
                        fix="The email is about you. Rewrite so the recipient's situation "
                            "carries the message.")]
    if ratio < 1.0:
        return [Finding("Focus", "WARN", detail, fix="Shift the balance toward them.")]
    return [Finding("Focus", "PASS", detail)]


def check_phrases(text):
    out = []
    hits = find_all(ANTI_PATTERNS, text)
    seen = set()
    for frag, why, pos in sorted(hits, key=lambda h: h[2]):
        key = frag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(Finding("Phrasing", "FAIL", why, quote_context(text, pos, len(frag)),
                           f"Cut “{frag}”."))
    if not out:
        out.append(Finding("Phrasing", "PASS", "No known anti-patterns."))
    return out


def check_spam_adjacent(text):
    hits = find_all(SPAM_ADJACENT, text)
    if not hits:
        return [Finding("Spam-adjacent", "PASS", "None found.")]
    frags = sorted({h[0].lower() for h in hits})
    return [Finding("Spam-adjacent", "WARN",
                    f"{len(frags)} phrase(s): {', '.join(frags)}",
                    fix="Low weight. Modern filters rank authentication and domain reputation "
                        "far above word lists — these matter as evidence of pressure language, "
                        "not because a keyword rule fires. Do not rewrite around this while "
                        "DMARC is broken.")]


def check_formatting(body):
    out = []
    if re.search(r"<(?:html|body|table|div|td|tr|p|br|img|a)\b", body, re.I):
        out.append(Finding("Formatting", "FAIL", "Contains HTML markup.",
                           fix="Send plain text. A full-width HTML template is the single "
                               "strongest bulk signal available."))
    bangs = body.count("!")
    if bangs > 1:
        out.append(Finding("Formatting", "WARN", f"{bangs} exclamation marks.",
                           fix="At most one, ideally none."))
    caps = [w for w in re.findall(r"\b[A-Z]{4,}\b", body)
            if w not in ("SPF", "DKIM", "DMARC", "SAAS", "HTTP", "JSON", "SQL", "API")]
    if caps:
        out.append(Finding("Formatting", "WARN", f"ALL-CAPS words: {', '.join(caps[:4])}",
                           fix="Reads as shouting and travels with bulk mail."))
    merge = find_all(MERGE_TOKENS, body)
    if merge:
        out.append(Finding("Formatting", "FAIL", "Unrendered merge token.",
                           merge[0][0], "The template leaked. Fix before sending anything."))
    if not out:
        out.append(Finding("Formatting", "PASS", "Plain text, no markup or leaked tokens."))
    return out


def check_readability(prose):
    grade, words, sents = readability(prose)
    if grade is None:
        return [Finding("Readability", "WARN", "Could not measure.")]
    longest = max((len(re.findall(r"[A-Za-z0-9']+", s))
                  for s in SENTENCE_SPLIT.split(prose) if s.strip()), default=0)
    detail = f"grade {grade}, {sents} sentence(s), longest {longest} words"
    if grade > 12:
        return [Finding("Readability", "WARN", detail,
                        fix="Above grade 12 on a phone is friction. Shorten sentences.")]
    if longest > 35:
        return [Finding("Readability", "WARN", detail,
                        fix=f"A {longest}-word sentence will not be read. Split it.")]
    return [Finding("Readability", "PASS", detail)]


def check_compliance(body, jurisdiction):
    out = []
    has_optout = bool(find_all(OPT_OUT, body))
    has_addr = bool(find_all(ADDRESS_HINTS, body))

    j = jurisdiction.lower()
    label = {"us": "CAN-SPAM", "ca": "CASL", "eu": "GDPR/ePrivacy", "uk": "GDPR/PECR"}.get(j, j.upper())

    if has_optout:
        out.append(Finding(f"Opt-out ({label})", "PASS", "Opt-out mechanism present."))
    else:
        sev = "FAIL" if j in ("us", "ca") else "WARN"
        out.append(Finding(f"Opt-out ({label})", sev, "No opt-out mechanism.",
                           fix="Required in the US and Canada, and good practice in the EU. A "
                               "plain-text line works and reads better than a footer: “If "
                               "you'd rather not hear from me, say so and I'll close the file.”"))

    if j in ("us", "ca"):
        if has_addr:
            out.append(Finding(f"Postal address ({label})", "PASS", "Address-like line found."))
        else:
            out.append(Finding(f"Postal address ({label})", "FAIL", "No physical postal address.",
                               fix="CAN-SPAM and CASL both require one. A PO box or registered "
                                   "agent address qualifies. This is the item cold email omits "
                                   "most often."))
    if j == "ca":
        out.append(Finding("Consent (CASL)", "INFO", "CASL requires express or implied consent.",
                           fix="Implied consent via a conspicuously published business address "
                               "requires that the message relate to the recipient's role. "
                               "Confirm that holds for this list."))
    if j in ("eu", "uk"):
        out.append(Finding("Lawful basis (GDPR)", "INFO",
                           "Legitimate interests requires a documented assessment before sending.",
                           fix="ePrivacy Art. 13 is the binding test and it varies by member "
                               "state — the UK permits B2B to corporate subscribers, Germany "
                               "effectively does not. Confirm the recipient countries."))
    return out


# ── Scoring and rendering ───────────────────────────────────────────────────────

WEIGHTS = {"FAIL": 12, "WARN": 5, "PASS": 0, "INFO": 0}
COLORS = {"PASS": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m", "INFO": "\033[90m"}
RESET = "\033[0m"


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def render(findings, score, path, use_color=True):
    def c(s):
        return f"{COLORS.get(s,'')}{s}{RESET}" if use_color else s

    W = 74
    print()
    print(f"  Cold email lint: {path}")
    print("  " + "─" * W)

    order, groups = [], {}
    for f in findings:
        if f.check not in groups:
            groups[f.check] = []
            order.append(f.check)
        groups[f.check].append(f)

    for check in order:
        for i, f in enumerate(groups[check]):
            name = check if i == 0 else ""
            print(f"  {c(f.status):<16} {name:<22} {f.detail}")
            if f.quote:
                for line in wrap(f'“{f.quote}”', W - 24):
                    print(f"  {'':<7} {'':<22} {line}")
            if f.fix:
                for k, line in enumerate(wrap(f.fix, W - 26)):
                    print(f"  {'':<7} {'':<20} {'→ ' if k == 0 else '  '}{line}")
        print()

    fails = sum(1 for f in findings if f.status == "FAIL")
    warns = sum(1 for f in findings if f.status == "WARN")
    print("  " + "─" * W)
    bar = "█" * (score // 5) + "░" * (20 - score // 5)
    print(f"  Score {score}/100  {bar}   {fails} FAIL, {warns} WARN")
    print()
    print("  A lint pass, not a verdict. A trigger-less email can score 100 — whether")
    print("  there is a real, checkable reason you emailed this person is a human call.")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", help="Path to the draft, or - for stdin.")
    ap.add_argument("--jurisdiction", default="us", choices=["us", "eu", "uk", "ca"])
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.draft == "-" else open(args.draft, encoding="utf-8").read()
    subject, body = parse_draft(raw)
    prose, _sig = split_signature(body)

    findings = []
    findings += check_subject(subject)
    findings += check_length(prose)
    findings += check_first_sentence(prose)
    findings += check_ask(prose)
    findings += check_balance(prose, subject)
    findings += check_links(prose)
    findings += check_phrases((subject or "") + "\n" + prose)
    findings += check_spam_adjacent((subject or "") + "\n" + body)
    findings += check_formatting(body)
    findings += check_readability(prose)
    findings += check_compliance(body, args.jurisdiction)

    penalty = sum(WEIGHTS[f.status] for f in findings)
    score = max(0, 100 - penalty)

    if args.as_json:
        print(json.dumps({
            "draft": args.draft, "subject": subject, "score": score,
            "jurisdiction": args.jurisdiction,
            "findings": [f.as_dict() for f in findings],
        }, indent=2))
    else:
        render(findings, score, args.draft, use_color=not args.no_color)

    sys.exit(1 if any(f.status == "FAIL" for f in findings) else 0)


if __name__ == "__main__":
    main()
