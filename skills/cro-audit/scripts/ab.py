#!/usr/bin/env python3
"""Experiment statistics for a CRO audit. Standard library only.

Subcommands
  size      how many visitors a test needs, and how long that takes here
  test      interpret a result: SRM check, confidence interval, then the lift
  funnel    step loss ranked by absolute users, not percentage
  peek-sim  simulate what checking the dashboard early does to false positives

The ordering inside each command is deliberate. `test` reports sample ratio
mismatch before it reports a winner, and the confidence interval before the
point estimate, because both are routinely skipped in that exact order.
"""

import argparse
import json
import math
import random
import sys
from statistics import NormalDist

ND = NormalDist()


# ---------------------------------------------------------------- helpers

def z(p):
    return ND.inv_cdf(p)


def two_sided_p(zstat):
    return 2 * (1 - ND.cdf(abs(zstat)))


def wilson(k, n, alpha=0.05):
    """Wilson score interval. Used instead of Wald because Wald is badly wrong
    at the small conversion counts this skill exists to deal with."""
    if n == 0:
        return (0.0, 0.0)
    za = z(1 - alpha / 2)
    p = k / n
    d = 1 + za * za / n
    centre = (p + za * za / (2 * n)) / d
    half = za * math.sqrt(p * (1 - p) / n + za * za / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe_diff(k1, n1, k2, n2, alpha=0.05):
    """CI for p2 - p1, Newcombe's score method (1998, method 10).

    More accurate than the Wald interval when counts are small, and it cannot
    produce a bound outside [-1, 1] the way Wald can."""
    l1, u1 = wilson(k1, n1, alpha)
    l2, u2 = wilson(k2, n2, alpha)
    p1, p2 = k1 / n1, k2 / n2
    lo = (p2 - p1) - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    hi = (p2 - p1) + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return (lo, hi)


def ratio_ci(k1, n1, k2, n2, alpha=0.05):
    """CI for the relative lift p2/p1 - 1, via the log ratio (delta method)."""
    if k1 == 0 or k2 == 0:
        return (float('-inf'), float('inf'))
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt((1 - p1) / (n1 * p1) + (1 - p2) / (n2 * p2))
    za = z(1 - alpha / 2)
    c = math.log(p2 / p1)
    return (math.exp(c - za * se) - 1, math.exp(c + za * se) - 1)


def n_per_arm(p1, p2, alpha=0.05, power=0.80):
    if p1 <= 0 or p2 <= 0 or p1 == p2:
        raise ValueError("baseline and target rate must be positive and different")
    za, zb = z(1 - alpha / 2), z(power)
    return (za + zb) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2


def parse_ratio(s):
    """'380/12000' -> (380, 12000)"""
    try:
        k, n = s.split('/')
        k, n = int(k.strip()), int(n.strip())
    except Exception:
        raise argparse.ArgumentTypeError(f"expected conversions/visitors, got {s!r}")
    if n <= 0 or k < 0 or k > n:
        raise argparse.ArgumentTypeError(f"nonsensical counts: {s!r}")
    return k, n


def pct(x, places=2):
    return f"{x * 100:.{places}f}%"


def signed_pct(x, places=1):
    return f"{'+' if x >= 0 else ''}{x * 100:.{places}f}%"


# ---------------------------------------------------------------- size

def cmd_size(a):
    p1 = a.baseline
    if a.mde_abs is not None:
        p2 = p1 + a.mde_abs
        mde_rel = a.mde_abs / p1
    else:
        mde_rel = a.mde_rel
        p2 = p1 * (1 + mde_rel)

    n = n_per_arm(p1, p2, a.alpha, a.power)
    total = n * a.arms
    out = {
        "baseline": p1, "target": p2, "mde_relative": mde_rel,
        "mde_absolute": p2 - p1, "alpha": a.alpha, "power": a.power,
        "arms": a.arms, "n_per_arm": math.ceil(n), "n_total": math.ceil(total),
    }

    lines = [
        f"Baseline           {pct(p1)}",
        f"Target             {pct(p2)}  ({signed_pct(mde_rel)} relative, "
        f"{signed_pct(p2 - p1, 2)} absolute)",
        f"alpha {a.alpha}  power {a.power}  arms {a.arms}",
        "",
        f"Visitors per arm   {math.ceil(n):,}",
        f"Total visitors     {math.ceil(total):,}",
    ]

    if a.weekly_traffic:
        weeks = total / a.weekly_traffic
        out["weeks"] = round(weeks, 1)
        out["weekly_traffic"] = a.weekly_traffic
        lines += ["", f"At {a.weekly_traffic:,} visitors/week: {weeks:.1f} weeks "
                      f"({weeks / 4.345:.1f} months)"]
        # The verdict is the point of this command.
        if weeks <= 4:
            v = "TESTABLE — concludes inside 4 weeks. Design it properly."
        elif weeks <= 12:
            v = ("SLOW — a full quarter for one answer. Worth it only for a decision "
                 "that genuinely blocks other work.")
        else:
            v = ("NOT TESTABLE — this test will never conclude at this traffic. "
                 "Ship on judgment or get evidence qualitatively; do not run it.")
        out["verdict"] = v.split(" — ")[0]
        lines += ["", v]
        if weeks > 4:
            det = detectable_at(p1, a.weekly_traffic * 4 / a.arms, a.alpha, a.power)
            if det:
                lines.append(f"In 4 weeks here you could only detect "
                             f"{signed_pct(det)} relative or larger.")
                out["detectable_in_4_weeks_rel"] = round(det, 4)

    if a.table:
        lines += ["", "Sensitivity — visitors per arm by relative MDE:"]
        for rel in (0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
            nn = n_per_arm(p1, p1 * (1 + rel), a.alpha, a.power)
            row = f"  {signed_pct(rel, 0):>6}   {math.ceil(nn):>12,}"
            if a.weekly_traffic:
                row += f"   {nn * a.arms / a.weekly_traffic:>6.1f} weeks"
            lines.append(row)

    emit(a, out, lines)


def detectable_at(p1, n_arm, alpha, power):
    """Smallest relative lift detectable with n_arm visitors per arm."""
    lo, hi = 1e-4, 5.0
    for _ in range(200):
        mid = (lo + hi) / 2
        need = n_per_arm(p1, p1 * (1 + mid), alpha, power)
        if need > n_arm:
            lo = mid
        else:
            hi = mid
    return hi if hi < 4.99 else None


# ---------------------------------------------------------------- test

def cmd_test(a):
    k1, n1 = a.a
    k2, n2 = a.b
    p1, p2 = k1 / n1, k2 / n2
    out = {"control": {"conversions": k1, "visitors": n1, "rate": p1},
           "variant": {"conversions": k2, "visitors": n2, "rate": p2}}
    lines = []

    # --- SRM first, on purpose.
    exp1 = (n1 + n2) * a.expected_split
    exp2 = (n1 + n2) * (1 - a.expected_split)
    chi2 = (n1 - exp1) ** 2 / exp1 + (n2 - exp2) ** 2 / exp2
    srm_p = two_sided_p(math.sqrt(chi2))  # exact for 1 df
    srm_fail = srm_p < 0.001
    out["srm"] = {"chi2": round(chi2, 3), "p": srm_p, "fail": srm_fail,
                  "expected_split": a.expected_split}

    lines += [
        "SAMPLE RATIO MISMATCH",
        f"  observed {n1:,} / {n2:,}   expected split {a.expected_split:.2f}",
        f"  chi2 = {chi2:.2f}, p = {srm_p:.4g}",
    ]
    if srm_fail:
        lines += [
            "  *** SRM FAIL (p < 0.001). Assignment or logging is broken.",
            "  *** Discard this result. Do not interpret the numbers below —",
            "  *** whatever broke the split is probably correlated with the outcome.",
        ]
    else:
        lines.append("  ok — split is consistent with the intended allocation")

    # --- interval before point estimate, also on purpose.
    dlo, dhi = newcombe_diff(k1, n1, k2, n2, a.alpha)
    rlo, rhi = ratio_ci(k1, n1, k2, n2, a.alpha)
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    zstat = (p2 - p1) / se if se > 0 else 0.0
    pval = two_sided_p(zstat)
    conf = int(round((1 - a.alpha) * 100))

    out.update({
        "absolute_diff": p2 - p1, "absolute_ci": [dlo, dhi],
        "relative_lift": (p2 / p1 - 1) if p1 > 0 else None,
        "relative_ci": [rlo, rhi], "p_value": pval, "z": zstat,
        "significant": pval < a.alpha and not srm_fail,
    })

    lines += [
        "",
        "RESULT",
        f"  control   {k1:>8,} / {n1:>9,}   {pct(p1)}",
        f"  variant   {k2:>8,} / {n2:>9,}   {pct(p2)}",
        "",
        f"  absolute difference  {signed_pct(p2 - p1, 2)}   "
        f"{conf}% CI [{signed_pct(dlo, 2)}, {signed_pct(dhi, 2)}]",
        f"  relative lift        {signed_pct(p2 / p1 - 1) if p1 > 0 else 'n/a':>7}   "
        f"{conf}% CI [{signed_pct(rlo)}, {signed_pct(rhi)}]",
        f"  p = {pval:.4g}",
    ]

    # --- the verdict, in the four flavours from experiment-design.md
    if srm_fail:
        verdict = ("BROKEN — SRM failed. No conclusion is available from this test.")
    elif pval >= a.alpha:
        verdict = (f"NO DETECTABLE DIFFERENCE. The interval spans zero. The honest "
                   f"summary is 'we could not detect a difference', not 'it did not "
                   f"work'.\n  To detect the observed {signed_pct(p2 / p1 - 1)} "
                   f"relative difference you would need "
                   f"{math.ceil(n_per_arm(p1, p2, a.alpha, a.power)):,} per arm; "
                   f"you have {n1:,} and {n2:,}.")
    elif abs(rhi - rlo) > 0.5:
        verdict = ("REAL BUT IMPRECISE. The interval excludes zero, so the direction "
                   "is probably right, but it spans a wide range — the point estimate "
                   "is not a number to plan with or put in a deck.")
    else:
        verdict = "REAL AND REASONABLY PRECISE. Direction and rough magnitude both hold."

    lines += ["", "VERDICT", "  " + verdict]

    if a.days is not None and a.days < 7:
        lines += ["", f"  NOTE: ran {a.days} days. Under one full weekly cycle — weekday "
                      "and weekend traffic differ in composition. Extend to 7 or 14 days "
                      "regardless of what the sample size says."]
        out["short_run"] = True

    emit(a, out, lines)


# ---------------------------------------------------------------- funnel

def cmd_funnel(a):
    steps = json.load(open(a.steps))
    if not isinstance(steps, list) or len(steps) < 2:
        sys.exit("steps.json must be an ordered list of at least two "
                 '{"name": ..., "users": ...} objects')
    for s in steps:
        if "name" not in s or "users" not in s:
            sys.exit(f"step missing name/users: {s!r}")

    top = steps[0]["users"]
    rows, out_rows = [], []
    for i in range(1, len(steps)):
        prev, cur = steps[i - 1], steps[i]
        lost = prev["users"] - cur["users"]
        step_cr = cur["users"] / prev["users"] if prev["users"] else 0.0
        cum = cur["users"] / top if top else 0.0
        rec = {
            "from": prev["name"], "to": cur["name"],
            "step_conversion": step_cr, "users_lost": lost,
            "cumulative_conversion": cum,
            "share_of_total_loss": lost / (top - steps[-1]["users"]) if top > steps[-1]["users"] else 0.0,
        }
        if a.value:
            # Ranking weight only. Not a recoverable amount — see the note below.
            rec["value_lost_ceiling"] = rec["value_lost"] = lost * a.value
        rows.append(rec)
        out_rows.append(rec)
        if step_cr > 1.0:
            rec["warning"] = ("step conversion above 100% — the event fires more than "
                              "once, or this step is reachable directly")

    lines = [f"{'step':<34}{'conv':>8}{'lost':>12}{'cum':>9}{'% of loss':>11}"]
    lines.append("-" * 74)
    for r in rows:
        lines.append(
            f"{(r['from'] + ' -> ' + r['to']):<34}"
            f"{pct(r['step_conversion'], 1):>8}"
            f"{r['users_lost']:>12,}"
            f"{pct(r['cumulative_conversion'], 2):>9}"
            f"{pct(r['share_of_total_loss'], 1):>11}"
        )
        if "warning" in r:
            lines.append(f"   !! {r['warning']}")

    ranked = sorted(rows, key=lambda r: r.get("value_lost", r["users_lost"]), reverse=True)
    lines += ["", "Ranked by absolute loss" + (" x value" if a.value else "") +
              " — NOT by percentage drop:"]
    for i, r in enumerate(ranked[:3], 1):
        v = f"  (ceiling ${r['value_lost']:,.0f})" if a.value else ""
        lines.append(f"  {i}. {r['from']} -> {r['to']}   {r['users_lost']:,} users{v}"
                     f"   {pct(r['share_of_total_loss'], 0)} of all loss")

    overall = steps[-1]["users"] / top if top else 0
    lines += ["", f"End to end: {steps[-1]['users']:,} / {top:,} = {pct(overall)}"]
    if a.value:
        ceiling = (top - steps[-1]["users"]) * a.value
        lines += [
            f"Ceiling on the whole funnel: ${ceiling:,.0f}",
            "  This is what every lost user would have been worth had they all converted.",
            "  They would not have. Use it to RANK steps against each other, never as a",
            "  recoverable number, and never put it in the report as an opportunity size.",
        ]

    emit(a, {"steps": out_rows, "overall_conversion": overall,
             "ranked": [f"{r['from']}->{r['to']}" for r in ranked]}, lines)


# ---------------------------------------------------------------- peek-sim

def cmd_peek_sim(a):
    """A/A simulation: no real difference, stop the first time p < alpha."""
    rng = random.Random(a.seed)
    za = z(1 - a.alpha / 2)
    checkpoints = sorted({round(a.n * (i + 1) / a.looks) for i in range(a.looks)})
    hits = 0
    for _ in range(a.trials):
        ca = cb = 0
        idx = 0
        for i in range(1, a.n + 1):
            ca += rng.random() < a.baseline
            cb += rng.random() < a.baseline
            if idx < len(checkpoints) and i == checkpoints[idx]:
                idx += 1
                pa, pb = ca / i, cb / i
                pp = (ca + cb) / (2 * i)
                se = math.sqrt(pp * (1 - pp) * (2 / i)) if pp > 0 else 0
                if se > 0 and abs(pb - pa) / se > za:
                    hits += 1
                    break
    rate = hits / a.trials
    lines = [
        f"A/A simulation — both arms at {pct(a.baseline)}, no real difference.",
        f"{a.trials:,} simulated tests, {a.n:,} visitors per arm, "
        f"stopping the first time p < {a.alpha}.",
        "",
        f"Looks at the data:        {a.looks}",
        f"False positive rate:      {pct(rate, 1)}",
        f"Nominal rate should be:   {pct(a.alpha, 1)}",
        "",
    ]
    if a.looks > 1:
        lines.append(f"Peeking {a.looks} times inflates the false positive rate by "
                     f"{rate / a.alpha:.1f}x. A team watching a dashboard daily during a "
                     f"three-week test is roughly here.")
    emit(a, {"looks": a.looks, "false_positive_rate": rate, "trials": a.trials}, lines)


# ---------------------------------------------------------------- io

def emit(a, obj, lines):
    if getattr(a, "json", False):
        print(json.dumps(obj, indent=2))
    else:
        print("\n".join(lines))


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--alpha", type=float, default=0.05)
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    s = sub.add_parser("size", help="visitors needed, and weeks that takes here")
    s.add_argument("--baseline", type=float, required=True,
                   help="current conversion rate as a proportion, e.g. 0.031")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--mde-rel", type=float, default=0.20,
                   help="smallest relative lift worth shipping (default 0.20)")
    g.add_argument("--mde-abs", type=float, help="smallest absolute lift, e.g. 0.005")
    s.add_argument("--power", type=float, default=0.80)
    s.add_argument("--arms", type=int, default=2)
    s.add_argument("--weekly-traffic", type=int,
                   help="visitors/week entering the test — gives duration and a verdict")
    s.add_argument("--table", action="store_true", help="sensitivity across MDEs")
    common(s)
    s.set_defaults(func=cmd_size)

    t = sub.add_parser("test", help="interpret a result: SRM, interval, then lift")
    t.add_argument("--a", type=parse_ratio, required=True, metavar="CONV/VISITORS",
                   help="control, e.g. 380/12000")
    t.add_argument("--b", type=parse_ratio, required=True, metavar="CONV/VISITORS",
                   help="variant, e.g. 410/11940")
    t.add_argument("--expected-split", type=float, default=0.5,
                   help="intended share of traffic to control (default 0.5)")
    t.add_argument("--power", type=float, default=0.80)
    t.add_argument("--days", type=int, help="days the test ran, for the cycle check")
    common(t)
    t.set_defaults(func=cmd_test)

    f = sub.add_parser("funnel", help="step loss ranked by absolute users")
    f.add_argument("--steps", required=True, help="ordered JSON list of {name, users}")
    f.add_argument("--value", type=float, help="value per conversion, for ranking")
    common(f)
    f.set_defaults(func=cmd_funnel)

    k = sub.add_parser("peek-sim", help="what early stopping does to false positives")
    k.add_argument("--looks", type=int, default=20)
    k.add_argument("--trials", type=int, default=1500)
    k.add_argument("--n", type=int, default=20000, help="visitors per arm at the horizon")
    k.add_argument("--baseline", type=float, default=0.03)
    k.add_argument("--seed", type=int, default=7)
    common(k)
    k.set_defaults(func=cmd_peek_sim)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
