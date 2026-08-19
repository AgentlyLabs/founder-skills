#!/usr/bin/env python3
"""Derive a deck palette from a company website.

    python3 extract_brand.py https://example.com --out brand.css
    python3 extract_brand.py --accent "#3b82f6" --out brand.css

Fetches the page and its stylesheets, finds the brand accent, then derives a
complete dark theme from that one hue using the HSL relationships in
references/design-system.md. Emits a `:root` block that overrides deck.css.

Stdlib only. The output is a starting point: verify it against the real site by
eye, because CSS cannot tell a brand accent from a warning red that happens to
appear often.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"

MAX_SHEETS = 8
MAX_BYTES = 2_000_000

# Custom-property names that usually hold the real brand color, best first.
NAME_PRIORITY = [
    "brand", "primary", "accent", "theme", "main", "action", "link", "highlight",
]
# Names that look brand-ish but are usually semantic status colors.
NAME_PENALTY = ["error", "danger", "warning", "success", "info", "destructive", "muted", "disabled"]


# --- colour parsing ---------------------------------------------------------

def parse_color(text: str):
    """Parse hex / rgb() / hsl() into (r, g, b) 0-255, or None."""
    text = text.strip().lower()

    m = re.fullmatch(r"#([0-9a-f]{3,8})", text)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        if len(h) in (6, 8):
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        return None

    m = re.fullmatch(r"rgba?\(([^)]+)\)", text)
    if m:
        parts = re.split(r"[,\s/]+", m.group(1).strip())
        try:
            vals = []
            for p in parts[:3]:
                vals.append(round(float(p[:-1]) * 255 / 100) if p.endswith("%") else round(float(p)))
            if len(vals) == 3 and all(0 <= v <= 255 for v in vals):
                return tuple(vals)
        except ValueError:
            return None
        return None

    m = re.fullmatch(r"hsla?\(([^)]+)\)", text)
    if m:
        parts = re.split(r"[,\s/]+", m.group(1).strip())
        try:
            hue = float(re.sub(r"deg$", "", parts[0])) % 360 / 360
            sat = float(parts[1].rstrip("%")) / 100
            lit = float(parts[2].rstrip("%")) / 100
            r, g, b = colorsys.hls_to_rgb(hue, lit, sat)
            return (round(r * 255), round(g * 255), round(b * 255))
        except (ValueError, IndexError):
            return None
    return None


def to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


def hls(rgb):
    r, g, b = [c / 255 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, l, s


def from_hls(h_deg, s, l) -> str:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360) / 360, l, s)
    return to_hex((round(r * 255), round(g * 255), round(b * 255)))


def is_usable_accent(rgb) -> bool:
    """Reject greys, near-blacks and near-whites: they cannot anchor a theme."""
    _, l, s = hls(rgb)
    return s >= 0.25 and 0.25 <= l <= 0.80


# --- fetching ---------------------------------------------------------------

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read(MAX_BYTES)
    charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def gather_css(url: str):
    """Return (html, combined_css, notes)."""
    notes = []
    html = fetch(url)
    sheets = []
    for href in re.findall(r'<link[^>]+rel=["\']?stylesheet["\']?[^>]*>', html, re.I):
        m = re.search(r'href=["\']([^"\']+)["\']', href, re.I)
        if m:
            sheets.append(urllib.parse.urljoin(url, m.group(1)))
    inline = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))

    css_parts = [inline]
    for sheet in sheets[:MAX_SHEETS]:
        try:
            css_parts.append(fetch(sheet))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            notes.append(f"could not fetch stylesheet {sheet}: {exc}")
    if len(sheets) > MAX_SHEETS:
        notes.append(f"{len(sheets)} stylesheets found; read the first {MAX_SHEETS}")
    return html, "\n".join(css_parts), notes


# --- accent selection -------------------------------------------------------

def score_name(name: str) -> int:
    n = name.lower()
    if any(bad in n for bad in NAME_PENALTY):
        return -50
    for rank, key in enumerate(NAME_PRIORITY):
        if key in n:
            return 100 - rank * 5
    return 0


def find_accent(html: str, css: str):
    """Return (accent_rgb, source_description, candidate_list)."""
    candidates = []

    # 1. Custom properties: the highest-signal source on any modern site.
    for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;{}]+)", css):
        rgb = parse_color(value)
        if rgb and is_usable_accent(rgb):
            base = score_name(name)
            if base > 0:
                candidates.append((base + 60, rgb, f"--{name}"))
            else:
                candidates.append((30, rgb, f"--{name}"))

    # 2. Declared theme colour.
    m = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if m:
        rgb = parse_color(m.group(1))
        if rgb and is_usable_accent(rgb):
            candidates.append((85, rgb, "meta theme-color"))

    # 3. Frequency across the CSS, as a fallback.
    counts = {}
    for literal in re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)", css):
        rgb = parse_color(literal)
        if rgb and is_usable_accent(rgb):
            counts[rgb] = counts.get(rgb, 0) + 1
    for rgb, n in sorted(counts.items(), key=lambda kv: -kv[1])[:6]:
        if n >= 3:
            candidates.append((min(40, 10 + n), rgb, f"used {n}x in CSS"))

    if not candidates:
        return None, "none found", []

    # Merge near-identical hues so one colour does not win on a technicality.
    merged = {}
    for score, rgb, src in candidates:
        key = tuple(v // 12 for v in rgb)
        if key not in merged or score > merged[key][0]:
            merged[key] = (score, rgb, src)
    ranked = sorted(merged.values(), key=lambda c: -c[0])
    best = ranked[0]
    return best[1], best[2], [(to_hex(r), s, src) for s, r, src in ranked[:6]]


GRAD_END_MIN_L = 0.55


def derive(accent_rgb) -> dict:
    """Build the full theme from the accent hue (design-system.md table)."""
    h, l, s = hls(accent_rgb)
    accent = to_hex(accent_rgb)
    # The gradient terminates in text on a near-black slide, so a dark brand
    # colour (navy, forest, maroon) would render the last word of every headline
    # almost invisible. Lift the final stop to a legibility floor, keeping hue
    # and saturation. --accent itself stays true to the brand for borders and
    # fills, where contrast is not the constraint.
    grad_end = accent if l >= GRAD_END_MIN_L else from_hls(h, max(s, 0.55), GRAD_END_MIN_L + 0.07)
    return {
        "--bg":         from_hls(h, 0.18, 0.06),
        "--surface":    from_hls(h, 0.12, 0.10),
        "--surface-2":  from_hls(h, 0.10, 0.08),
        "--border":     from_hls(h, 0.08, 0.14),
        "--ink":        from_hls(h, 0.06, 0.98),
        "--body":       from_hls(h, 0.08, 0.80),
        "--muted":      from_hls(h, 0.08, 0.45),
        "--accent":     accent,
        "--accent-dim": from_hls(h, 0.30, 0.55),
        "--grad": (f"linear-gradient(100deg, {from_hls(h, 0.25, 0.90)} 0%, "
                   f"{from_hls(h, 0.45, 0.84)} 45%, {grad_end} 100%)"),
    }


def find_fonts(css: str):
    families = []
    for decl in re.findall(r"font-family\s*:\s*([^;{}]+)", css, re.I):
        first = decl.split(",")[0].strip().strip('"\'')
        low = first.lower()
        if first and low not in {"inherit", "initial", "unset"} and not low.startswith("var("):
            if first not in families:
                families.append(first)
    return families[:5]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Derive a deck palette from a website.")
    ap.add_argument("url", nargs="?", help="Company website URL")
    ap.add_argument("--accent", help="Skip fetching; derive the theme from this colour")
    ap.add_argument("--out", help="Write the :root CSS block here (default: stdout)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON instead of CSS")
    args = ap.parse_args(argv)

    if not args.url and not args.accent:
        ap.error("give a URL or --accent")

    notes, source, ranked, fonts = [], "--accent flag", [], []

    if args.accent:
        accent = parse_color(args.accent)
        if not accent:
            sys.exit(f"error: could not parse colour {args.accent!r}")
    else:
        url = args.url if "://" in args.url else "https://" + args.url
        try:
            html, css, notes = gather_css(url)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            sys.exit(f"error: could not fetch {url}: {exc}\n"
                     f"Pass --accent '#rrggbb' to derive a theme without fetching.")
        accent, source, ranked = find_accent(html, css)
        fonts = find_fonts(css)
        if accent is None:
            sys.exit("error: found no usable brand colour in the site CSS.\n"
                     "The palette may live in images. Pick a colour by eye and pass "
                     "--accent '#rrggbb'.")

    theme = derive(accent)

    if args.as_json:
        payload = json.dumps({"accent": to_hex(accent), "source": source, "theme": theme,
                              "candidates": ranked, "fonts": fonts, "notes": notes}, indent=2)
        print(payload)
        return 0

    lines = [
        "/* Derived from " + (args.url if args.url else "--accent") + " */",
        "/* Accent " + to_hex(accent) + " (" + source + "). Verify against the real site by eye. */",
        ":root {",
    ]
    for key, value in theme.items():
        lines.append(f"  {key + ':':<14}{value};")
    lines.append("}")
    css_out = "\n".join(lines) + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(css_out)
        print(f"wrote {args.out}")
    else:
        print(css_out)

    # Diagnostics go to stderr so `--out -` style piping stays clean.
    print(f"\naccent  {to_hex(accent)}  via {source}", file=sys.stderr)
    if ranked:
        print("runners-up:", file=sys.stderr)
        for hexv, score, src in ranked[1:]:
            print(f"   {hexv}  score {score:<4} {src}", file=sys.stderr)
    if fonts:
        print(f"fonts seen: {', '.join(fonts)}", file=sys.stderr)
    for note in notes:
        print(f"note: {note}", file=sys.stderr)
    print("\nLink this after deck.css so it overrides the defaults.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
