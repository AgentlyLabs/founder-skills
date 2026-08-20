#!/usr/bin/env python3
"""Audit a sending domain's email authentication posture.

Resolves SPF, DKIM, DMARC, MX, MTA-STS and TLS-RPT via `dig` and reports each check as
PASS / WARN / FAIL with the specific fix. No third-party dependencies.

    python3 check_domain.py example.com
    python3 check_domain.py example.com --json
    python3 check_domain.py example.com --selectors s1,s2,mycustom

Exit status is 1 if any check FAILs, else 0.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys

# Selectors published by common sending platforms. DKIM selector names are chosen by the
# sender, so they cannot be derived — they have to be probed.
DEFAULT_SELECTORS = [
    "google",           # Google Workspace
    "selector1",        # Microsoft 365
    "selector2",
    "s1", "s2",         # SendGrid / generic
    "k1",               # Mailchimp / Mandrill
    "k2",
    "dkim",
    "default",
    "mail",
    "smtp",
    "zoho",
    "mandrill",
    "mailjet",
    "pm",               # Postmark
    "resend",
    "amazonses",
    "protonmail",
    "fm1",              # Fastmail
]

# Counted against SPF's 10-lookup limit (RFC 7208 §4.6.4).
SPF_LOOKUP_MECHANISMS = ("include:", "a:", "mx:", "ptr", "exists:", "redirect=")


class Result:
    def __init__(self, name, status, detail, fix=None, record=None):
        self.name = name
        self.status = status          # PASS | WARN | FAIL | INFO
        self.detail = detail
        self.fix = fix
        self.record = record

    def as_dict(self):
        return {
            "check": self.name,
            "status": self.status,
            "detail": self.detail,
            "fix": self.fix,
            "record": self.record,
        }


def dig(name, rtype, timeout=6):
    """Return a list of answer strings, TXT chunks joined and unquoted."""
    try:
        proc = subprocess.run(
            ["dig", "+short", "+time=3", "+tries=1", rtype, name],
            capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    answers = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if rtype == "TXT":
            # dig renders long TXT records as multiple quoted chunks on one line.
            chunks = re.findall(r'"([^"]*)"', line)
            line = "".join(chunks) if chunks else line.strip('"')
        answers.append(line)
    return answers


def check_mx(domain):
    mx = dig(domain, "MX")
    if not mx:
        return Result(
            "MX", "FAIL", "No MX records — the domain cannot receive mail.",
            "Publish MX records. A sending domain with no MX looks disposable to "
            "receivers, and replies have nowhere to go.",
        )
    return Result("MX", "PASS", f"{len(mx)} record(s): {', '.join(mx[:3])}", record=mx)


def check_spf(domain):
    txt = dig(domain, "TXT")
    spf = [r for r in txt if r.lower().startswith("v=spf1")]

    if not spf:
        return Result(
            "SPF", "FAIL", "No SPF record found.",
            'Publish a TXT record at the root: "v=spf1 include:<your-provider> ~all". '
            "Google requires SPF or DKIM from all senders.",
        )
    if len(spf) > 1:
        return Result(
            "SPF", "FAIL", f"{len(spf)} SPF records found — this is a permerror, not a merge.",
            "Merge them into a single v=spf1 record. Receivers treat multiple records as "
            "a permanent error and may fail the check outright.",
            record=spf,
        )

    record = spf[0]
    lookups = sum(record.lower().count(m) for m in SPF_LOOKUP_MECHANISMS)
    # Bare `a` / `mx` mechanisms (no colon) also cost a lookup each.
    tokens = record.lower().split()
    lookups += sum(1 for t in tokens if t in ("a", "mx", "+a", "+mx"))

    notes = [f"{lookups} DNS lookup(s) declared"]
    status, fix = "PASS", None

    if re.search(r"[+]all\b", record):
        status = "FAIL"
        notes.append("qualifier is +all — this authorizes any sender")
        fix = "Replace +all with ~all (soft fail) or -all (hard fail). +all is equivalent "\
              "to publishing no policy at all."
    elif re.search(r"-all\b", record):
        notes.append("hard fail (-all)")
    elif re.search(r"~all\b", record):
        notes.append("soft fail (~all)")
    elif re.search(r"\?all\b", record):
        status = "WARN"
        notes.append("neutral (?all) — no policy asserted")
        fix = "Use ~all or -all so receivers have a policy to act on."
    else:
        status = "WARN"
        notes.append("no all-qualifier present")
        fix = "Terminate the record with ~all or -all."

    if lookups > 10:
        status = "FAIL"
        notes.append(f"exceeds the 10-lookup limit (RFC 7208 §4.6.4)")
        fix = (f"Reduce to 10 or fewer DNS lookups — currently ~{lookups}. Over the limit "
               "is a permerror and the check fails. Flatten or drop unused includes.")
    elif lookups >= 8:
        if status == "PASS":
            status = "WARN"
        notes.append("close to the 10-lookup limit")
        fix = fix or (f"~{lookups} of 10 lookups used. Adding one more provider will break "
                      "this record. Audit the includes now.")

    return Result("SPF", status, "; ".join(notes), fix, record=record)


def check_dkim(domain, selectors):
    found = []
    for sel in selectors:
        name = f"{sel}._domainkey.{domain}"
        answers = dig(name, "TXT")
        for a in answers:
            if "p=" in a and ("v=DKIM1" in a or "k=rsa" in a):
                keylen = None
                m = re.search(r"p=([A-Za-z0-9+/=]+)", a)
                if m:
                    # Rough modulus size from the base64 SubjectPublicKeyInfo length.
                    b64len = len(m.group(1))
                    keylen = 1024 if b64len < 250 else 2048
                found.append({"selector": sel, "bits": keylen})
                break
        # A CNAME'd selector (common with ESPs) resolves through to the TXT above.

    if not found:
        return Result(
            "DKIM", "FAIL",
            f"No DKIM key found across {len(selectors)} probed selector(s).",
            "Enable DKIM signing in your sending platform and publish the key it gives "
            "you. If DKIM is configured under a custom selector, re-run with "
            "--selectors <name>. Note this probe cannot prove absence — only that the "
            "common selectors are empty.",
        )

    weak = [f["selector"] for f in found if f["bits"] == 1024]
    detail = "key(s) at selector(s): " + ", ".join(
        f"{f['selector']} (~{f['bits']}-bit)" for f in found
    )
    if weak:
        return Result(
            "DKIM", "WARN", detail + " — 1024-bit key detected",
            f"Rotate {', '.join(weak)} to a 2048-bit key. 1024 is still accepted but is "
            "discounted by some receivers.",
            record=found,
        )
    return Result("DKIM", "PASS", detail, record=found)


def check_dmarc(domain):
    txt = dig(f"_dmarc.{domain}", "TXT")
    dmarc = [r for r in txt if r.lower().startswith("v=dmarc1")]

    if not dmarc:
        return Result(
            "DMARC", "FAIL", "No DMARC record at _dmarc." + domain,
            'Publish a TXT record at _dmarc.' + domain + ': '
            '"v=DMARC1; p=none; rua=mailto:dmarc@' + domain + '". Start at p=none *with* '
            "a reporting address, read the reports, then move to quarantine or reject.",
        )
    if len(dmarc) > 1:
        return Result(
            "DMARC", "FAIL", f"{len(dmarc)} DMARC records — receivers will ignore all of them.",
            "Keep exactly one v=DMARC1 record.", record=dmarc,
        )

    record = dmarc[0]
    tags = {}
    for part in record.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            tags[k.strip().lower()] = v.strip()

    policy = tags.get("p", "").lower()
    rua = tags.get("rua")
    adkim = tags.get("adkim", "r")
    aspf = tags.get("aspf", "r")
    pct = tags.get("pct", "100")

    notes = [f"p={policy or 'missing'}", f"alignment adkim={adkim} aspf={aspf}", f"pct={pct}"]
    status, fix = "PASS", None

    if not policy:
        status = "FAIL"
        fix = "The p= tag is required. Add p=none at minimum."
    elif policy == "none" and not rua:
        status = "FAIL"
        notes.append("no rua — nothing enforced and nobody reading the reports")
        fix = ("p=none with no rua= is functionally identical to having no DMARC. Add "
               f"rua=mailto:dmarc@{domain} so authentication failures become visible.")
    elif policy == "none":
        status = "WARN"
        notes.append("monitor-only; reporting is configured")
        fix = ("Reports are flowing — good. Once they show your legitimate mail passing, "
               "move to p=quarantine and then p=reject.")
    elif policy in ("quarantine", "reject"):
        notes.append("enforcing")
        if pct != "100":
            status = "WARN"
            fix = f"pct={pct} means the policy only applies to {pct}% of failing mail. "\
                  "Move to 100 once you are confident."
    else:
        status = "WARN"
        fix = f"Unrecognized policy value p={policy}."

    if not rua and status == "PASS":
        status = "WARN"
        notes.append("no rua")
        fix = "Add rua= so you receive aggregate reports."

    return Result("DMARC", status, "; ".join(notes), fix, record=record)


def check_mta_sts(domain):
    txt = dig(f"_mta-sts.{domain}", "TXT")
    sts = [r for r in txt if r.lower().startswith("v=stsv1")]
    if sts:
        return Result("MTA-STS", "PASS", sts[0], record=sts[0])
    return Result(
        "MTA-STS", "INFO", "Not configured.",
        "Optional. Enforces TLS for inbound mail. Not a cold-outbound requirement, but a "
        "positive signal on a domain's operational maturity.",
    )


def check_tls_rpt(domain):
    txt = dig(f"_smtp._tls.{domain}", "TXT")
    rpt = [r for r in txt if r.lower().startswith("v=tlsrptv1")]
    if rpt:
        return Result("TLS-RPT", "PASS", rpt[0], record=rpt[0])
    return Result("TLS-RPT", "INFO", "Not configured.", "Optional TLS failure reporting.")


def subdomain_advice(domain):
    """A domain with MX and a website is likely the primary domain."""
    labels = domain.split(".")
    is_subdomain = len(labels) > 2 and labels[0] not in ("www",)
    if is_subdomain:
        return Result(
            "Sending domain", "PASS",
            f"{domain} looks like a dedicated subdomain — reputation is isolated.",
        )
    return Result(
        "Sending domain", "WARN",
        f"{domain} appears to be a primary domain.",
        "Send cold outbound from a dedicated subdomain (e.g. outbound." + domain + ") or a "
        "separate domain. Otherwise a reputation hit from outbound also degrades password "
        "resets, invoices, and every other transactional message.",
    )


COLORS = {"PASS": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m", "INFO": "\033[90m"}
RESET = "\033[0m"


def render(domain, results, use_color=True):
    def c(status):
        if not use_color:
            return status
        return f"{COLORS.get(status, '')}{status}{RESET}"

    width = 72
    print()
    print(f"  Sending-domain audit: {domain}")
    print("  " + "─" * width)

    for r in results:
        print(f"  {c(r.status):<16} {r.name:<16} {r.detail}")
        if r.fix:
            for i, line in enumerate(wrap(r.fix, width - 20)):
                print(f"  {'':<7} {'→ ' if i == 0 else '  '}{line}")
        print()

    fails = [r for r in results if r.status == "FAIL"]
    warns = [r for r in results if r.status == "WARN"]

    print("  " + "─" * width)
    if fails:
        print(f"  {len(fails)} FAIL, {len(warns)} WARN — "
              "fix the failures before sending. Unauthenticated mail is not read.")
        print(f"  Start here: {fails[0].name}")
    elif warns:
        print(f"  0 FAIL, {len(warns)} WARN — authenticated, with gaps worth closing.")
    else:
        print("  All checks pass. Authentication is not the bottleneck.")
    print()


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


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("domain")
    ap.add_argument("--selectors", help="Comma-separated extra DKIM selectors to probe.")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    if not shutil.which("dig"):
        sys.exit("error: `dig` not found. Install bind-utils / dnsutils.")

    domain = args.domain.strip().lower()
    domain = re.sub(r"^https?://", "", domain).split("/")[0].lstrip("@")

    selectors = list(DEFAULT_SELECTORS)
    if args.selectors:
        selectors = [s.strip() for s in args.selectors.split(",") if s.strip()] + selectors

    results = [
        check_spf(domain),
        check_dkim(domain, selectors),
        check_dmarc(domain),
        check_mx(domain),
        subdomain_advice(domain),
        check_mta_sts(domain),
        check_tls_rpt(domain),
    ]

    if args.as_json:
        print(json.dumps({
            "domain": domain,
            "checks": [r.as_dict() for r in results],
            "fail_count": sum(1 for r in results if r.status == "FAIL"),
            "warn_count": sum(1 for r in results if r.status == "WARN"),
        }, indent=2))
    else:
        render(domain, results, use_color=not args.no_color)

    sys.exit(1 if any(r.status == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    main()
