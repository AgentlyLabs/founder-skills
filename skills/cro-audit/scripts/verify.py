#!/usr/bin/env python3
"""Check that a CRO report is made of measurements rather than opinions.

    python3 verify.py report.md measurements.json

Exits 0 only when every finding cites at least one measurement key, every cited
key exists, and every cited value matches what was actually measured.

That last rule is the one that matters. It is what stops a number from drifting
between the measurement and the sentence describing it -- which is how confident,
wrong findings get into an otherwise careful report.

Report contract (see references/report-template.md):

    **Finding stated as a fact**
    `[m: form.field_count = 11, mobile.autocomplete_missing = 7]`
    Mechanism, estimate, and a Ship / Test / Decide verdict.

A finding is a line that is entirely bold. Its citation must appear within the
three following non-empty lines.
"""

import argparse
import json
import re
import sys

FINDING_RE = re.compile(r"^\s*\*\*(.+?)\*\*\s*:?\s*$")
CITE_RE = re.compile(r"\[m:\s*(.+?)\]")
PAIR_RE = re.compile(r"([A-Za-z_][\w]*(?:\.[\w\[\]]+)+)\s*(?:=\s*([^,]+))?")

# Claims from evidence-base.md tier 3. Their presence means the report is padding.
FOLKLORE = [
    (r"\bbutton colou?r\b|\b(?:red|green|orange|blue) button\b", "button colour"),
    (r"\bexit[- ]intent\b", "exit-intent popup as a default good"),
    (r"\breduce (?:the number of )?clicks\b|\bfewer clicks\b", "click-count reduction"),
    (r"\bheat ?map (?:shows|proves|reveals)\b", "heatmap treated as evidence"),
    (r"\bcreate urgency\b|\badd (?:a )?(?:countdown|urgency)\b", "manufactured urgency"),
    (r"\b\d+ (?:cro |conversion )?principles\b", "fixed-count principle list"),
    (r"\babove the fold\b(?!.{0,80}(?:measured|viewport|375|1366))", "'above the fold' as a law"),
]

# A percentage stated as an EFFECT with no range next to it. Targeting matters:
# a bare "%" is usually a measured position or share, not a claimed lift, and
# flagging those trains the reader to ignore the warning.
LIFT_RE = re.compile(
    r"([+\-]?\d+(?:\.\d+)?\s?%)(?=[^.]{0,60}\b(?:lift|increase|improve|gain|uplift|"
    r"better|higher|more signups|more conversions)\b)"
    r"|\b(?:lift|increase|improve|gain|uplift|by)\b[^.]{0,40}?([+\-]?\d+(?:\.\d+)?\s?%)",
    re.I)
RANGE_HINT = re.compile(r"\bCI\b|–|—|\bto\b|\brange\b|\bbetween\b|-{1,2}\s?\d|"
                        r"\bceiling\b|\bup to\b|\bno defensible\b|\bcannot\b", re.I)


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        out[prefix] = obj
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def values_agree(cited, actual):
    c = cited.strip().strip('`"\'').rstrip('.')
    if isinstance(actual, bool):
        return c.lower() in ("true", "false") and (c.lower() == "true") == actual
    if isinstance(actual, (int, float)):
        m = re.search(r"-?\d+(?:\.\d+)?", c.replace(",", ""))
        if not m:
            return False
        n = float(m.group(0))
        if c.rstrip().endswith("%") and 0 < abs(actual) <= 1:
            n /= 100.0
        return abs(n - float(actual)) < max(1e-9, abs(float(actual)) * 0.005)
    if actual is None:
        return c.lower() in ("null", "none", "not measured", "n/a")
    if isinstance(actual, list):
        return str(len(actual)) == c or c.lower() in str(actual).lower()
    return c.lower() in str(actual).lower() or str(actual).lower() in c.lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report")
    ap.add_argument("measurements")
    ap.add_argument("--allow-uncited", action="store_true",
                    help="downgrade uncited findings to warnings (use only for a draft)")
    a = ap.parse_args()

    try:
        lines = open(a.report).read().splitlines()
        measured = flatten(json.load(open(a.measurements)))
    except Exception as e:
        sys.exit(f"could not read inputs: {type(e).__name__}: {e}")

    fails, warns = [], []
    findings = 0
    cited_keys = set()

    for i, line in enumerate(lines):
        m = FINDING_RE.match(line)
        if not m or line.strip().startswith("**Why") or len(m.group(1)) < 12:
            continue
        findings += 1
        title = m.group(1)

        window = []
        j = i + 1
        while j < len(lines) and len(window) < 3:
            if lines[j].strip():
                window.append(lines[j])
            j += 1
        blob = " ".join(window)

        cites = CITE_RE.findall(blob)
        if not cites:
            (warns if a.allow_uncited else fails).append(
                (i + 1, "UNCITED", f"finding has no [m: ...] citation: {title[:70]}"))
            continue

        for cite in cites:
            pairs = PAIR_RE.findall(cite)
            if not pairs:
                fails.append((i + 1, "MALFORMED", f"citation parses to no keys: [m: {cite}]"))
            for key, val in pairs:
                cited_keys.add(key)
                if key not in measured:
                    near = [k for k in measured if k.startswith(key.split(".")[0] + ".")][:3]
                    hint = f" (did you mean: {', '.join(near)})" if near else ""
                    fails.append((i + 1, "NO SUCH KEY",
                                  f"{key} is not in measurements.json{hint}"))
                elif val and not values_agree(val, measured[key]):
                    fails.append((i + 1, "VALUE MISMATCH",
                                  f"{key}: report says {val.strip()}, "
                                  f"measured {measured[key]!r}"))

        nums = [g for match in LIFT_RE.findall(blob) for g in match if g]
        if nums and not RANGE_HINT.search(blob):
            warns.append((i + 1, "POINT ESTIMATE",
                          f"'{nums[0].strip()}' claimed as an effect with no range"))

    body = "\n".join(lines).lower()
    for pat, name in FOLKLORE:
        m = re.search(pat, body)
        if m:
            ln = body[:m.start()].count("\n") + 1
            warns.append((ln, "FOLKLORE", f"{name} — see references/evidence-base.md tier 3"))

    if findings == 0:
        warns.append((0, "NO FINDINGS",
                      "no finding blocks parsed — a finding is a line that is entirely "
                      "bold; see references/report-template.md"))
    if not re.search(r"could not be measured|gaps?\b", body):
        warns.append((0, "NO GAPS SECTION",
                      "report declares no unmeasured checks; an unmeasured check is not "
                      "a passed check"))
    if not re.search(r"\bship\b", body) or not re.search(r"\bdecide\b|\btest\b", body):
        warns.append((0, "NO VERDICTS",
                      "findings should carry a Ship / Test / Decide verdict"))

    print(f"{findings} findings, {len(cited_keys)} distinct measurement keys cited "
          f"of {len(measured)} measured\n")

    for tag, items in (("FAIL", fails), ("WARN", warns)):
        for ln, kind, msg in items:
            where = f"{a.report}:{ln}" if ln else a.report
            print(f"{tag}  {kind:<14} {where}  {msg}")

    if fails or warns:
        print()
    if fails:
        print(f"FAILED — {len(fails)} finding(s) not backed by the measurements.")
        print("Every claim in the report must be traceable to a measured value.")
        return 1
    print(f"PASSED — every finding cites a real measurement"
          + (f", {len(warns)} warning(s) to look at." if warns else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
