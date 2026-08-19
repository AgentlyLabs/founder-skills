#!/usr/bin/env python3
"""Deterministic analysis over raw Google Search Console API responses.

Implements modules 1-5 from references/analyses.md: the property CTR curve,
striking-distance queries, CTR underperformance, keyword cannibalization, and
traffic-decay classification.

Input files are raw `searchanalytics.query` responses, i.e. JSON of the shape:

    {"rows": [{"keys": ["/page", "a query"], "clicks": 12,
               "impressions": 340, "ctr": 0.035, "position": 11.4}, ...]}

A bare list of rows is also accepted. The `--dimensions` flag must match the
order the dimensions were requested in, since `keys` is positional.

Only the standard library is used, so this runs anywhere Python 3.8+ does.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

# --- Thresholds -------------------------------------------------------------
# Defaults calibrated in references/analyses.md. Each is exposed as a CLI flag
# because the right value genuinely depends on site scale.

MIN_BUCKET_ROWS = 30          # rows needed before a CTR-curve bucket is trusted
STRIKING_MIN_POS = 8.0
STRIKING_MAX_POS = 20.0
STRIKING_MIN_IMPR = 100
STRIKING_TARGET_POS = 5       # deliberately not 1; see analyses.md module 2
CTR_GAP_RATIO = 0.60          # flag CTR at or below 60% of bucket median
CTR_MIN_IMPR = 100
CANNIBAL_MIN_IMPR = 100
CANNIBAL_MIN_SHARE = 0.15
DECAY_MIN_BASELINE_CLICKS = 50
DECAY_DROP = 0.25
FLAT_BAND = 0.10              # +/-10% counts as "flat" for classification
POSITION_FLAT_BAND = 1.0      # positions within 1.0 count as unchanged


# --- Loading ----------------------------------------------------------------

def load_rows(path: str) -> List[Dict[str, Any]]:
    """Read a GSC response file and return its rows."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        rows = payload.get("rows", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError(f"{path}: expected an object with 'rows' or a list of rows")
    if not isinstance(rows, list):
        raise ValueError(f"{path}: 'rows' is not a list")
    return rows


def keyed(rows: Iterable[Dict[str, Any]], dimensions: List[str]) -> List[Dict[str, Any]]:
    """Attach named dimension values to each row, from the positional `keys`."""
    out = []
    for row in rows:
        keys = row.get("keys") or []
        if len(keys) < len(dimensions):
            continue  # malformed row; skipping beats guessing which dimension is missing
        record = {
            "clicks": float(row.get("clicks", 0) or 0),
            "impressions": float(row.get("impressions", 0) or 0),
            "position": float(row.get("position", 0) or 0),
        }
        # Recompute CTR rather than trusting the field, so aggregates stay consistent.
        record["ctr"] = record["clicks"] / record["impressions"] if record["impressions"] else 0.0
        for index, name in enumerate(dimensions):
            record[name] = keys[index]
        out.append(record)
    return out


# --- Aggregation ------------------------------------------------------------

def aggregate(rows: Iterable[Dict[str, Any]], by: str) -> Dict[str, Dict[str, float]]:
    """Collapse rows onto one dimension.

    Position is impression-weighted: averaging GSC's average positions with equal
    weight is wrong (see gsc-api-surface.md, caveat 2).
    """
    acc: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"clicks": 0.0, "impressions": 0.0, "_pos_weighted": 0.0}
    )
    for row in rows:
        key = row.get(by)
        if key is None:
            continue
        bucket = acc[key]
        bucket["clicks"] += row["clicks"]
        bucket["impressions"] += row["impressions"]
        bucket["_pos_weighted"] += row["position"] * row["impressions"]

    result = {}
    for key, bucket in acc.items():
        impressions = bucket["impressions"]
        result[key] = {
            "clicks": bucket["clicks"],
            "impressions": impressions,
            "position": bucket["_pos_weighted"] / impressions if impressions else 0.0,
            "ctr": bucket["clicks"] / impressions if impressions else 0.0,
        }
    return result


# --- Module 1: property CTR curve -------------------------------------------

def build_ctr_curve(rows: List[Dict[str, Any]], min_rows: int = MIN_BUCKET_ROWS) -> Dict[int, Dict[str, float]]:
    """Median CTR per integer position bucket, from the property's own data.

    Median rather than mean: a handful of brand queries at 60% CTR would drag a
    mean upward and make the entire site look like it underperforms.
    """
    buckets: Dict[int, List[float]] = defaultdict(list)
    for row in rows:
        if row["impressions"] <= 0 or row["position"] <= 0:
            continue
        position = int(round(row["position"]))
        if 1 <= position <= 20:
            buckets[position].append(row["ctr"])

    curve = {}
    for position, values in sorted(buckets.items()):
        if len(values) >= min_rows:
            curve[position] = {"median_ctr": statistics.median(values), "rows": len(values)}
    return curve


def curve_lookup(curve: Dict[int, Dict[str, float]], position: int) -> Optional[float]:
    """Median CTR at a position, interpolating across gaps in the curve.

    Sparse curves are normal on smaller properties: some position buckets never
    reach the minimum row count. Snapping to the *nearest* populated bucket is
    tempting but badly wrong across a gap -- with buckets at 3 and 8 populated,
    a position-5 lookup would return position 3's median, which on a real CTR
    decay curve is roughly double the truth and inflates every downstream impact
    estimate. Interpolating between the bracketing buckets keeps the estimate in
    the right neighborhood; nearest-bucket is used only outside the known range,
    where there is nothing to interpolate between.
    """
    if not curve:
        return None
    if position in curve:
        return curve[position]["median_ctr"]

    below = [p for p in curve if p < position]
    above = [p for p in curve if p > position]
    if below and above:
        low, high = max(below), min(above)
        weight = (position - low) / (high - low)
        return curve[low]["median_ctr"] + weight * (curve[high]["median_ctr"] - curve[low]["median_ctr"])

    nearest = min(curve.keys(), key=lambda p: (abs(p - position), p))
    return curve[nearest]["median_ctr"]


# --- Module 2: striking distance --------------------------------------------

def striking_distance(rows, curve, min_impr=STRIKING_MIN_IMPR, target=STRIKING_TARGET_POS):
    target_ctr = curve_lookup(curve, target)
    if target_ctr is None:
        return []

    findings = []
    for row in rows:
        if not (STRIKING_MIN_POS <= row["position"] <= STRIKING_MAX_POS):
            continue
        if row["impressions"] < min_impr:
            continue
        uplift = target_ctr - row["ctr"]
        if uplift <= 0:
            continue  # already beating the target position's typical CTR
        findings.append({
            "query": row.get("query"),
            "page": row.get("page"),
            "impressions": round(row["impressions"]),
            "clicks": round(row["clicks"]),
            "position": round(row["position"], 1),
            "ctr": round(row["ctr"], 4),
            "target_position": target,
            "target_ctr": round(target_ctr, 4),
            "est_incremental_clicks": round(row["impressions"] * uplift, 1),
        })
    findings.sort(key=lambda f: f["est_incremental_clicks"], reverse=True)
    return findings


def group_by_page(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Roll query-level findings up to the page that would actually be worked on."""
    grouped: Dict[str, Dict[str, Any]] = {}
    for finding in findings:
        page = finding.get("page") or "(unknown)"
        entry = grouped.setdefault(page, {
            "page": page, "queries": [], "est_incremental_clicks": 0.0, "impressions": 0,
        })
        entry["queries"].append(finding["query"])
        entry["est_incremental_clicks"] += finding["est_incremental_clicks"]
        entry["impressions"] += finding["impressions"]

    out = []
    for entry in grouped.values():
        entry["query_count"] = len(entry["queries"])
        entry["queries"] = entry["queries"][:10]
        entry["est_incremental_clicks"] = round(entry["est_incremental_clicks"], 1)
        out.append(entry)
    out.sort(key=lambda e: e["est_incremental_clicks"], reverse=True)
    return out


# --- Module 3: CTR underperformance -----------------------------------------

def ctr_underperformance(rows, curve, ratio=CTR_GAP_RATIO, min_impr=CTR_MIN_IMPR):
    findings = []
    for row in rows:
        if row["impressions"] < min_impr or not (0 < row["position"] <= 20):
            continue
        expected = curve_lookup(curve, int(round(row["position"])))
        if expected is None or expected <= 0:
            continue
        if row["ctr"] <= expected * ratio:
            findings.append({
                "query": row.get("query"),
                "page": row.get("page"),
                "impressions": round(row["impressions"]),
                "position": round(row["position"], 1),
                "ctr": round(row["ctr"], 4),
                "expected_ctr": round(expected, 4),
                "gap_pct": round((1 - row["ctr"] / expected) * 100, 1),
                "est_incremental_clicks": round(row["impressions"] * (expected - row["ctr"]), 1),
                "check_before_recommending": [
                    "SERP feature or AI Overview absorbing the click",
                    "brand mismatch on the query",
                    "intent mismatch between query and page",
                ],
            })
    findings.sort(key=lambda f: f["est_incremental_clicks"], reverse=True)
    return findings


# --- Module 4: cannibalization ----------------------------------------------

def cannibalization(rows, min_impr=CANNIBAL_MIN_IMPR, min_share=CANNIBAL_MIN_SHARE):
    """Queries where two or more URLs each hold a meaningful impression share.

    This detects *candidates* only. Impression share alone is not evidence —
    confirm via rank alternation across the window before calling it real.
    """
    by_query: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("query") and row.get("page"):
            by_query[row["query"]].append(row)

    findings = []
    for query, entries in by_query.items():
        total = sum(entry["impressions"] for entry in entries)
        if total < min_impr or len(entries) < 2:
            continue
        competing = [entry for entry in entries if entry["impressions"] / total >= min_share]
        if len(competing) < 2:
            continue
        competing.sort(key=lambda entry: entry["impressions"], reverse=True)
        findings.append({
            "query": query,
            "total_impressions": round(total),
            "url_count": len(competing),
            "urls": [{
                "page": entry["page"],
                "impressions": round(entry["impressions"]),
                "share": round(entry["impressions"] / total, 3),
                "position": round(entry["position"], 1),
                "clicks": round(entry["clicks"]),
            } for entry in competing],
            "status": "candidate",
            "confirm_with": (
                "Check whether the ranking URL alternates across the window, or both "
                "URLs sit past position 10, or the titles are near-duplicates. "
                "Do not treat impression share alone as proof."
            ),
        })
    findings.sort(key=lambda f: f["total_impressions"], reverse=True)
    return findings


# --- Module 5: decay classification -----------------------------------------

def _direction(current: float, baseline: float, band: float = FLAT_BAND) -> str:
    if baseline <= 0:
        return "up" if current > 0 else "flat"
    change = (current - baseline) / baseline
    if change > band:
        return "up"
    if change < -band:
        return "down"
    return "flat"


def _position_direction(current: float, baseline: float) -> str:
    # Lower position values are better, so the sign is inverted versus metrics.
    delta = current - baseline
    if delta > POSITION_FLAT_BAND:
        return "down"
    if delta < -POSITION_FLAT_BAND:
        return "up"
    return "flat"


def classify(clicks_dir: str, impressions_dir: str, position_dir: str) -> str:
    """Map the three-metric signature onto a mechanism (SKILL.md Step 5)."""
    if clicks_dir == "down" and impressions_dir == "flat" and position_dir == "flat":
        return "CTR loss - SERP layout, AI Overview, or title change"
    if clicks_dir == "down" and impressions_dir == "down" and position_dir == "down":
        return "Ranking loss - content, links, or competitor gains"
    if clicks_dir == "down" and impressions_dir == "down" and position_dir == "flat":
        return "Demand loss or seasonality - check year-over-year before acting"
    if clicks_dir == "down" and impressions_dir == "flat" and position_dir == "down":
        return "Rank slide within page 1 - often precedes a larger drop"
    if clicks_dir == "flat" and impressions_dir == "up" and position_dir == "down":
        return "Broader but weaker matching - new queries diluting the average"
    return "Mixed signature - inspect manually"


def decay(current_rows, previous_rows, year_ago_rows=None,
          min_baseline_clicks=DECAY_MIN_BASELINE_CLICKS, drop=DECAY_DROP):
    current = aggregate(current_rows, "page")
    previous = aggregate(previous_rows, "page")
    year_ago = aggregate(year_ago_rows, "page") if year_ago_rows else {}

    findings = []
    for page, prev in previous.items():
        if prev["clicks"] < min_baseline_clicks:
            continue  # a fall from 4 clicks to 1 is a 75% drop and means nothing
        curr = current.get(page, {"clicks": 0.0, "impressions": 0.0, "position": 0.0, "ctr": 0.0})
        change = (curr["clicks"] - prev["clicks"]) / prev["clicks"]
        if change > -drop:
            continue

        signature = classify(
            _direction(curr["clicks"], prev["clicks"]),
            _direction(curr["impressions"], prev["impressions"]),
            _position_direction(curr["position"], prev["position"]),
        )

        finding = {
            "page": page,
            "clicks_current": round(curr["clicks"]),
            "clicks_previous": round(prev["clicks"]),
            "clicks_change_pct": round(change * 100, 1),
            "impressions_current": round(curr["impressions"]),
            "impressions_previous": round(prev["impressions"]),
            "position_current": round(curr["position"], 1),
            "position_previous": round(prev["position"], 1),
            "mechanism": signature,
        }

        if page in year_ago:
            prior = year_ago[page]
            yoy = ((curr["clicks"] - prior["clicks"]) / prior["clicks"]) if prior["clicks"] else None
            finding["clicks_year_ago"] = round(prior["clicks"])
            finding["yoy_change_pct"] = round(yoy * 100, 1) if yoy is not None else None
            # If the same window last year was similarly low, the decline is seasonal.
            if yoy is not None and yoy > -FLAT_BAND:
                finding["seasonality_note"] = (
                    "Clicks are level with the same window last year - likely seasonal. "
                    "Recommend waiting rather than manufacturing a fix."
                )
        else:
            finding["seasonality_note"] = "No year-ago data supplied; seasonality unchecked."

        findings.append(finding)

    findings.sort(key=lambda f: f["clicks_previous"] - f["clicks_current"], reverse=True)
    return findings


# --- CLI --------------------------------------------------------------------

def summarize(results: Dict[str, Any]) -> str:
    positions = sorted(int(p) for p in results["ctr_curve"])
    target = results["meta"]["thresholds"]["target_position"]
    lines = [
        "",
        "=== GSC analysis summary ===",
        f"Rows analyzed:             {results['meta']['rows_current']}",
        f"CTR curve buckets built:   {len(positions)}"
        + (f" (positions {positions[0]}-{positions[-1]})" if positions else " - insufficient data"),
        f"Striking-distance queries: {len(results['striking_distance'])}"
        f" across {len(results['striking_distance_by_page'])} pages",
        f"CTR underperformers:       {len(results['ctr_underperformance'])}",
        f"Cannibalization candidates:{len(results['cannibalization']):>3}",
        f"Decaying pages:            {len(results['decay'])}",
    ]

    if positions and target not in positions:
        lines.append(
            f"\nNOTE: no populated CTR bucket at target position {target}; its CTR was "
            f"interpolated. Impact estimates depend on it, so treat them as directional."
        )

    total = sum(f["est_incremental_clicks"] for f in results["striking_distance"])
    if total:
        lines.append(f"Est. striking-distance upside: +{total:,.0f} clicks/period at position "
                     f"{target}")

    top = results["striking_distance_by_page"][:5]
    if top:
        lines.append("\nTop opportunity pages:")
        for entry in top:
            lines.append(f"  +{entry['est_incremental_clicks']:>8,.0f}  "
                         f"{entry['query_count']:>3} queries  {entry['page']}")

    if not positions:
        lines.append(
            "\nWARNING: no CTR-curve bucket reached the minimum row count, so no impact "
            "estimates were produced. Widen the window or lower --min-bucket-rows."
        )
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze Google Search Console data for SEO audit findings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Row 'keys' are positional, so --dimensions must match the order the "
               "dimensions were requested in.",
    )
    parser.add_argument("--current", required=True, help="Current-window GSC response JSON")
    parser.add_argument("--previous", help="Previous-window response, for decay analysis")
    parser.add_argument("--year-ago", dest="year_ago", help="Same window last year, for seasonality")
    parser.add_argument("--dimensions", default="page,query",
                        help="Dimension order in the response (default: page,query)")
    parser.add_argument("--out", help="Write full findings JSON here (default: stdout)")
    parser.add_argument("--min-bucket-rows", type=int, default=MIN_BUCKET_ROWS)
    parser.add_argument("--min-impressions", type=int, default=STRIKING_MIN_IMPR)
    parser.add_argument("--target-position", type=int, default=STRIKING_TARGET_POS)
    parser.add_argument("--quiet", action="store_true", help="Suppress the summary")
    args = parser.parse_args(argv)

    dimensions = [d.strip() for d in args.dimensions.split(",") if d.strip()]
    if "page" not in dimensions:
        parser.error("--dimensions must include 'page'")

    try:
        current = keyed(load_rows(args.current), dimensions)
        previous = keyed(load_rows(args.previous), dimensions) if args.previous else None
        year_ago = keyed(load_rows(args.year_ago), dimensions) if args.year_ago else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not current:
        print("error: no usable rows in the current-window file", file=sys.stderr)
        return 1

    curve = build_ctr_curve(current, args.min_bucket_rows)
    striking = striking_distance(current, curve, args.min_impressions, args.target_position)

    results = {
        "meta": {
            "rows_current": len(current),
            "dimensions": dimensions,
            "thresholds": {
                "min_bucket_rows": args.min_bucket_rows,
                "min_impressions": args.min_impressions,
                "target_position": args.target_position,
                "ctr_gap_ratio": CTR_GAP_RATIO,
                "cannibal_min_share": CANNIBAL_MIN_SHARE,
            },
        },
        "ctr_curve": {str(k): v for k, v in curve.items()},
        "striking_distance": striking,
        "striking_distance_by_page": group_by_page(striking),
        "ctr_underperformance": ctr_underperformance(current, curve),
        "cannibalization": cannibalization(current) if "query" in dimensions else [],
        "decay": decay(current, previous, year_ago) if previous else [],
    }

    payload = json.dumps(results, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
        if not args.quiet:
            print(f"Findings written to {args.out}")
    else:
        print(payload)

    if not args.quiet:
        print(summarize(results), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
