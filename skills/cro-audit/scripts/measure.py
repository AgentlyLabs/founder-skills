#!/usr/bin/env python3
"""Measure a page for a CRO audit. Standard library only.

    python3 measure.py https://example.com/trial \
        --source-copy "Automate invoice reconciliation" --assets -o measurements.json

Writes every measured value under a stable key. Findings in the report cite
those keys, and scripts/verify.py refuses to pass a report whose findings cite
keys that are not in here.

This covers the static and network layer only. Anything that needs layout --
fold position, occlusion, tap target size, contrast -- has to come from a real
browser; references/page-checks.md carries the snippets. Merge those results in
under the same keys rather than keeping a second file.
"""

import argparse
import gzip
import json
import re
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

UA_DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")

MAX_BYTES = 8 * 1024 * 1024
MAX_ASSETS = 40

STOPWORDS = set("""a an the and or but if then than that this these those of for to in on at by with
from as is are was were be been being it its your you we our us they them their he she his her
what which who whom how when where why all any both each few more most other some such no nor not
only own same so too very can will just get got make made now new about into over under out up down
""".split())

# Words that fill a headline without saying what the product is.
BUZZWORDS = set("""platform solution solutions leverage seamless seamlessly empower empowering
transform transforming transformation revolutionize revolutionary innovative innovation
next-generation nextgen cutting-edge state-of-the-art world-class best-in-class robust scalable
holistic synergy streamline streamlined optimize optimized supercharge unlock unleash elevate
reimagine future ecosystem experience experiences journey enable enabling powerful simple simply
effortless smarter better faster easy easily amazing incredible ultimate premier leading trusted
""".split())

TRUST_PATTERNS = [
    (r"\bno credit card\b", "no-card"),
    (r"\bcancel any ?time\b", "cancel-anytime"),
    (r"\bmoney[- ]back\b|\brefund\b", "refund"),
    (r"\bsoc ?2\b|\biso ?27001\b|\bhipaa\b|\bgdpr\b|\bpci\b", "compliance"),
    (r"\bssl\b|\bencrypt", "encryption"),
    (r"\bwe (?:will )?never (?:share|sell|spam)\b|\bno spam\b|\bunsubscribe any", "privacy"),
    (r"\b\d[\d,\.]*[km]?\+? (?:customers|users|teams|companies|developers|businesses)\b", "customer-count"),
    (r"\bfree (?:trial|forever|plan|tier)\b", "free-tier"),
    (r"\bguarantee\b", "guarantee"),
    (r"\b(?:g2|capterra|trustpilot|product hunt)\b", "review-site"),
]

PRICE_RE = re.compile(r"(?:[$£€]\s?\d[\d,]*(?:\.\d{2})?|\b\d+\s?(?:usd|eur|gbp)\b"
                      r"|\bper (?:seat|user|month|year)\b|\b/\s?(?:mo|month|yr|year|user|seat)\b)", re.I)
TRIAL_RE = re.compile(r"\b(\d+)[- ]day (?:free )?trial\b|\bfree trial\b", re.I)
CARD_RE = re.compile(r"\bno credit card\b|\bcredit card required\b|\bcard required\b", re.I)

# CTA labels that describe the mechanic rather than the outcome.
WEAK_CTA = {"submit", "send", "go", "click here", "continue", "next", "ok", "sign up",
            "signup", "register", "subscribe", "buy now", "purchase", "learn more"}

NUMERIC_HINTS = ("zip", "postal", "phone", "tel", "card", "cvv", "cvc", "amount",
                 "quantity", "seats", "employees", "size", "year")


# ------------------------------------------------------------------ fetching

def fetch(url, ua, timeout=20):
    if urlparse(url).scheme not in ("http", "https"):
        sys.exit(f"refusing non-http(s) URL: {url}")
    req = Request(url, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    chain = []
    with urlopen(req, timeout=timeout) as r:
        raw = r.read(MAX_BYTES)
        enc = (r.headers.get("Content-Encoding") or "").lower()
        if "gzip" in enc:
            body = gzip.decompress(raw)
        elif "deflate" in enc:
            body = zlib.decompress(raw, -zlib.MAX_WBITS)
        else:
            body = raw
        charset = "utf-8"
        ct = r.headers.get("Content-Type") or ""
        m = re.search(r"charset=([\w-]+)", ct, re.I)
        if m:
            charset = m.group(1)
        if r.url != url:
            chain.append(r.url)
        return {
            "status": r.status,
            "final_url": r.url,
            "redirected": r.url != url,
            "transfer_bytes": len(raw),
            "decoded_bytes": len(body),
            "compressed": bool(enc),
            "html": body.decode(charset, errors="replace"),
            "headers": {k.lower(): v for k, v in r.headers.items()},
        }


def asset_size(url, ua, timeout=15):
    try:
        req = Request(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
        with urlopen(req, timeout=timeout) as r:
            n = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                n += len(chunk)
                if n > MAX_BYTES:
                    break
            return {"url": url, "bytes": n, "status": r.status}
    except Exception as e:
        return {"url": url, "bytes": None, "error": type(e).__name__}


# ------------------------------------------------------------------ parsing

class Page(HTMLParser):
    """Collects only what the checks in page-checks.md actually need."""

    SKIP_TEXT = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.node = 0                 # monotonic element counter, for distances
        self.stack = []
        self.region = []              # nav / header / footer / main / form nesting
        self.title = None
        self.in_title = False
        self.meta = {}
        self.headings = []            # (level, text, node)
        self.links = []               # dicts
        self.forms = []
        self.buttons = []
        self.scripts = []
        self.styles = []
        self.images = []
        self.text_parts = []          # (text, region, node)
        self.labels = {}              # for= -> text
        self._label_for = None
        self._label_buf = []
        self._cur_form = None
        self._cur_link = None
        self._cur_btn = None
        self._heading = None
        self.html_lang = None

    # -- region helpers
    def _region(self):
        for r in ("form", "footer", "nav", "header"):
            if r in self.region:
                return r
        return "body"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.node += 1
        n = self.node
        self.stack.append(tag)

        if tag == "html":
            self.html_lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag in ("nav", "header", "footer"):
            self.region.append(tag)
        elif tag == "form":
            self.region.append("form")
            self._cur_form = {"action": a.get("action"), "method": a.get("method", "get"),
                              "node": n, "fields": [], "submit": None}
            self.forms.append(self._cur_form)
        elif tag in ("h1", "h2", "h3"):
            self.headings.append([int(tag[1]), "", n])
            self._heading = self.headings[-1]
        elif tag == "a":
            self._cur_link = {"href": a.get("href"), "text": "", "region": self._region(),
                              "node": n, "role": a.get("role"), "class": a.get("class", "")}
            self.links.append(self._cur_link)
        elif tag == "label":
            self._label_for = a.get("for")
            self._label_buf = []
        elif tag in ("input", "textarea", "select"):
            typ = (a.get("type") or ("textarea" if tag == "textarea" else "select")).lower()
            if typ in ("hidden",):
                return
            f = {
                "tag": tag, "type": typ, "name": a.get("name") or a.get("id") or "",
                "id": a.get("id"), "required": "required" in a,
                "autocomplete": a.get("autocomplete"),
                "inputmode": a.get("inputmode"),
                "placeholder": a.get("placeholder"),
                "aria_label": a.get("aria-label"),
                "node": n, "region": self._region(),
            }
            if typ in ("submit", "button", "image"):
                b = {"label": a.get("value") or a.get("aria-label") or "", "node": n,
                     "region": self._region(), "kind": "input"}
                self.buttons.append(b)
                if self._cur_form and typ == "submit":
                    self._cur_form["submit"] = b
            elif self._cur_form is not None:
                self._cur_form["fields"].append(f)
            else:
                # a field outside any <form> -- common with JS frameworks, which
                # often submit via a handler and never declare a form element
                orphan = next((x for x in self.forms if x.get("orphan")), None)
                if orphan is None:
                    orphan = {"action": None, "method": None, "node": n,
                              "fields": [], "submit": None, "orphan": True}
                    self.forms.append(orphan)
                orphan["fields"].append(f)
        elif tag == "button":
            self._cur_btn = {"label": "", "node": n, "region": self._region(),
                             "kind": "button", "type": (a.get("type") or "submit").lower()}
            self.buttons.append(self._cur_btn)
            if self._cur_form and self._cur_btn["type"] == "submit" and not self._cur_form["submit"]:
                self._cur_form["submit"] = self._cur_btn
        elif tag == "script":
            self.scripts.append({"src": a.get("src"), "async": "async" in a,
                                 "defer": "defer" in a, "type": a.get("type"), "node": n})
        elif tag == "link" and (a.get("rel") or "").lower().find("stylesheet") >= 0:
            self.styles.append({"href": a.get("href"), "media": a.get("media"), "node": n})
        elif tag == "img":
            self.images.append({"src": a.get("src"), "alt": a.get("alt"),
                                "loading": a.get("loading"), "node": n})

    def handle_endtag(self, tag):
        if self.stack and tag in self.stack:
            while self.stack:
                t = self.stack.pop()
                if t == tag:
                    break
        if tag == "title":
            self.in_title = False
        elif tag in ("nav", "header", "footer", "form") and tag in self.region:
            self.region.reverse()
            self.region.remove(tag)
            self.region.reverse()
            if tag == "form":
                self._cur_form = None
        elif tag in ("h1", "h2", "h3"):
            if self._heading is not None:
                self._heading[1] = " ".join(self._heading[1].split())
            self._heading = None
        elif tag == "a":
            self._cur_link = None
        elif tag == "button":
            self._cur_btn = None
        elif tag == "label":
            text = " ".join("".join(self._label_buf).split())
            if self._label_for:
                self.labels[self._label_for] = text
            self._label_for, self._label_buf = None, []

    def handle_data(self, d):
        if self.in_title:
            self.title = (self.title or "") + d
            return
        if self.stack and self.stack[-1] in self.SKIP_TEXT:
            return
        if self._label_for is not None:
            self._label_buf.append(d)
        if self._heading is not None:
            self._heading[1] += d
        if self._cur_link is not None:
            self._cur_link["text"] += d
        if self._cur_btn is not None:
            self._cur_btn["label"] += d
        s = d.strip()
        if s:
            self.text_parts.append((s, self._region(), self.node))


# ------------------------------------------------------------------ analysis

def words(s):
    return [w for w in re.findall(r"[a-z0-9']+", (s or "").lower())
            if len(w) > 2 and w not in STOPWORDS]


def stem(w):
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def message_match(source, h1, subhead, first_para):
    src = [stem(w) for w in words(source)]
    if not src:
        return {"score": None, "note": "no --source-copy supplied; check not run",
                "missing_terms": None, "matched_terms": None}
    hay = {stem(w) for w in words(" ".join([h1 or "", subhead or "", first_para or ""]))}
    hit = [w for w in src if w in hay]
    miss = [w for w in src if w not in hay]
    return {
        "score": round(len(hit) / len(src), 3),
        "matched_terms": sorted(set(hit)),
        "missing_terms": sorted(set(miss)),
        "note": ("every content word from the source appears" if not miss else
                 "terms from the traffic source do not appear on the page"),
    }


def analyse(url, page, resp, args):
    text_all = " ".join(t for t, _, _ in page.text_parts)
    text_lower = text_all.lower()
    h1s = [h[1] for h in page.headings if h[0] == 1 and h[1]]
    h1 = h1s[0] if h1s else None
    h1_node = next((h[2] for h in page.headings if h[0] == 1 and h[1]), None)

    subhead = None
    if h1_node is not None:
        after = [t for t, r, n in page.text_parts if n > h1_node and len(t.split()) >= 4]
        subhead = after[0] if after else None
    first_para = next((t for t, r, n in page.text_parts if len(t.split()) >= 8), None)

    # ---- forms
    forms = []
    for f in page.forms:
        fields = []
        for fl in f["fields"]:
            label = (page.labels.get(fl["id"] or "") or fl["aria_label"] or "").strip()
            fields.append({
                "name": fl["name"], "type": fl["type"], "required": fl["required"],
                "autocomplete": fl["autocomplete"], "inputmode": fl["inputmode"],
                "label": label or None,
                "placeholder_only": not label and bool(fl["placeholder"]),
            })
        forms.append({
            "action": f["action"], "orphan": bool(f.get("orphan")),
            "field_count": len(fields), "required_count": sum(1 for x in fields if x["required"]),
            "submit_label": " ".join((f["submit"] or {}).get("label", "").split()) or None,
            "fields": fields,
        })
    primary = max(forms, key=lambda f: f["field_count"], default=None)

    # ---- mobile / input defects
    type_errors, ac_missing, no_label = [], [], []
    for f in forms:
        for fl in f["fields"]:
            n = (fl["name"] or "").lower()
            lab = (fl["label"] or "").lower()
            hay = n + " " + lab
            if fl["type"] == "text":
                if "email" in hay:
                    type_errors.append({"field": fl["name"], "is": "text", "should_be": "email"})
                elif any(k in hay for k in ("phone", "tel", "mobile")):
                    type_errors.append({"field": fl["name"], "is": "text", "should_be": "tel"})
                elif any(k in hay for k in NUMERIC_HINTS) and not fl["inputmode"]:
                    type_errors.append({"field": fl["name"], "is": "text",
                                        "should_be": 'inputmode="numeric"'})
            if fl["type"] in ("text", "email", "tel", "password", "number", "select") \
                    and not fl["autocomplete"]:
                ac_missing.append(fl["name"])
            if not fl["label"]:
                no_label.append(fl["name"])

    vp = page.meta.get("viewport", "")
    viewport = {
        "present": bool(vp), "content": vp or None,
        "width_device": "width=device-width" in vp.replace(" ", ""),
        "blocks_zoom": bool(re.search(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b", vp)),
    }

    # ---- attention ratio
    def is_real(l):
        h = (l["href"] or "").strip()
        return h and not h.startswith(("#", "javascript:", "mailto:", "tel:"))
    real = [l for l in page.links if is_real(l)]
    dests = {urljoin(url, l["href"]) for l in real}
    by_region = {}
    for l in real:
        by_region[l["region"]] = by_region.get(l["region"], 0) + 1
    goals = args.goals
    attention = {
        "links": len(dests), "links_including_repeats": len(real),
        "nav_links": by_region.get("nav", 0) + by_region.get("header", 0),
        "footer_links": by_region.get("footer", 0),
        "body_links": by_region.get("body", 0),
        "goals": goals,
        "ratio": round(len(dests) / goals, 1) if goals else None,
        "scope_note": "landing-page check only; meaningless on a homepage or docs page",
    }

    # ---- CTAs
    ctas = []
    for b in page.buttons:
        lab = " ".join((b.get("label") or "").split())
        if lab:
            ctas.append(lab)
    for l in real:
        cls = (l.get("class") or "")
        if re.search(r"\bbtn\b|button|cta", cls, re.I):
            lab = " ".join(l["text"].split())
            if lab:
                ctas.append(lab)
    primary_cta = (primary or {}).get("submit_label") or (ctas[0] if ctas else None)
    cta = {
        "primary_label": primary_cta,
        "count": len(ctas),
        "distinct_labels": sorted(set(ctas)),
        "distinct_label_count": len(set(ctas)),
        "weak_label": bool(primary_cta and primary_cta.strip().lower() in WEAK_CTA),
    }

    # ---- price and commitment
    price_hits = PRICE_RE.findall(text_all)
    trial = TRIAL_RE.search(text_all)
    price = {
        "on_page": bool(price_hits),
        "examples": sorted(set(price_hits))[:6],
        "pricing_link": any(re.search(r"/pricing|/plans", (l["href"] or ""), re.I) or
                            re.search(r"\bpricing\b|\bplans\b", l["text"], re.I) for l in real),
        "trial_stated": bool(trial),
        "trial_text": trial.group(0) if trial else None,
        "card_required_stated": bool(CARD_RE.search(text_all)),
    }

    # ---- trust markers and their distance to the submit control
    # Proximity is judged by which container the marker sits in, not by how many
    # elements away it is -- element distance is not structural closeness, and a
    # footer badge measured as "14 nodes from the button" is a false pass.
    markers = []
    for pat, name in TRUST_PATTERNS:
        for t, region, node in page.text_parts:
            m = re.search(pat, t.lower())
            if m:
                markers.append({"kind": name, "node": node, "region": region,
                                "text": t[max(0, m.start() - 10):m.end() + 30].strip()})
                break
    submit_node = None
    if primary:
        pf = next((f for f in page.forms if not f.get("orphan") and f["submit"]), None)
        submit_node = pf["submit"]["node"] if pf else None
    if submit_node is None and page.buttons:
        submit_node = page.buttons[0]["node"]
    in_form = [m["kind"] for m in markers if m["region"] == "form"]
    footer_only = bool(markers) and all(m["region"] == "footer" for m in markers)
    dist = None
    if submit_node is not None and markers:
        near = [abs(m["node"] - submit_node) for m in markers if m["node"] is not None]
        dist = min(near) if near else None
    trust = {
        "markers": [m["kind"] for m in markers],
        "marker_count": len(markers),
        "in_form_container": in_form,
        "near_submit": bool(in_form),
        "footer_only": footer_only,
        "submit_node": submit_node,
        "element_distance_to_submit": dist,
        "distance_note": "informational only -- near_submit is decided by container, "
                         "not by this number",
        "detail": markers,
    }

    # ---- hero language
    h1_words = words(h1)
    hero_words = words(" ".join([h1 or "", subhead or ""]))
    buzz_h1 = [w for w in h1_words if w in BUZZWORDS]
    buzz_hero = [w for w in hero_words if w in BUZZWORDS]
    ratio = round(len(buzz_hero) / len(hero_words), 2) if hero_words else None
    hero = {
        "h1": h1, "h1_count": len(h1s),
        "h1_word_count": len(h1.split()) if h1 else 0,
        "subhead": subhead,
        "subhead_word_count": len(subhead.split()) if subhead else 0,
        "buzzwords_in_h1": buzz_h1,
        "buzzwords_in_hero": buzz_hero,
        "buzzword_ratio": ratio,
        "buzzword_heavy": ratio is not None and ratio >= 0.30,
        "note": "a ratio, not a verdict -- run the five-second test on the screenshot "
                "and decide whether a stranger can name the category",
    }

    # ---- weight / blocking
    blocking_js = [s for s in page.scripts if s["src"] and not (s["async"] or s["defer"])]
    speed = {
        "transfer_bytes": resp["transfer_bytes"],
        "decoded_bytes": resp["decoded_bytes"],
        "compressed": resp["compressed"],
        "script_count": len(page.scripts),
        "render_blocking_scripts": len(blocking_js),
        "stylesheet_count": len(page.styles),
        "image_count": len(page.images),
        "images_without_lazy": sum(1 for i in page.images if not i["loading"]),
        "lcp_field_ms": None, "inp_field_ms": None, "cls_field": None,
        "field_data_note": "not measured here -- pull CrUX; lab numbers mislead",
    }

    word_count = len(text_all.split())
    js_rendered = word_count < 60 and len(page.scripts) >= 3

    out = {
        "_meta": {
            "url": url, "measured_with": "scripts/measure.py",
            "user_agent": "mobile" if args.mobile else "desktop",
            "layer": "static+network only -- rendered values must be merged in",
        },
        "page": {
            "url": url, "final_url": resp["final_url"], "status": resp["status"],
            "redirected": resp["redirected"], "title": (page.title or "").strip() or None,
            "lang": page.html_lang, "word_count": word_count,
            "meta_description": page.meta.get("description"),
            "likely_js_rendered": js_rendered,
        },
        "match": message_match(args.source_copy, h1, subhead, first_para),
        "hero": hero,
        "form": {
            "count": len(forms),
            "field_count": (primary or {}).get("field_count", 0),
            "required_count": (primary or {}).get("required_count", 0),
            "submit_label": (primary or {}).get("submit_label"),
            "fields": (primary or {}).get("fields", []),
            "unjustified": None,
            "unjustified_note": "set by hand -- a field is justified only if the promise "
                                "cannot be delivered without it, or a human acts on it "
                                "within 48h",
            "all_forms": forms,
        },
        "mobile": {
            "viewport_meta": viewport,
            "input_type_errors": len(type_errors),
            "input_type_error_detail": type_errors,
            "autocomplete_missing": len(ac_missing),
            "autocomplete_missing_fields": ac_missing,
            "fields_without_label": len(no_label),
            "tap_targets_under_44": None,
            "horizontal_overflow": None,
            "rendered_note": "tap targets and overflow need the browser layer",
        },
        "attention": attention,
        "cta": {**cta, "above_fold_375": None, "above_fold_1366": None,
                "occluded": None, "contrast_ratio": None,
                "rendered_note": "fold, occlusion and contrast need the browser layer"},
        "price": price,
        "trust": trust,
        "speed": speed,
    }

    if js_rendered:
        out["_gaps"] = ["page returned almost no text without JavaScript -- every "
                        "content-based value here is unreliable; take them from the "
                        "browser layer instead"]
    return out


def add_assets(out, url, page, ua, workers=8):
    urls, seen = [], set()
    for coll, key in ((page.scripts, "src"), (page.styles, "href"), (page.images, "src")):
        for item in coll:
            u = item.get(key)
            if not u:
                continue
            full = urljoin(url, u)
            if full.startswith(("http://", "https://")) and full not in seen:
                seen.add(full)
                urls.append(full)
    urls = urls[:MAX_ASSETS]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda u: asset_size(u, ua), urls))
    got = [r for r in results if r["bytes"] is not None]
    total = sum(r["bytes"] for r in got) + out["speed"]["transfer_bytes"]
    out["speed"].update({
        "requests_measured": len(results),
        "requests_failed": len(results) - len(got),
        "total_bytes_measured": total,
        "total_kb": round(total / 1024),
        "heaviest": sorted(got, key=lambda r: -r["bytes"])[:5],
        "truncated": len(seen) > MAX_ASSETS,
    })
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url")
    p.add_argument("--source-copy", help="the ad headline, email subject, or query that "
                                         "sent the traffic -- without it, message match "
                                         "cannot run")
    p.add_argument("--goals", type=int, default=1,
                   help="distinct conversion actions on the page (default 1)")
    p.add_argument("--assets", action="store_true", help="fetch subresources for weight")
    p.add_argument("--mobile", action="store_true", help="request as a mobile UA")
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("-o", "--out", help="write measurements.json here")
    args = p.parse_args()

    ua = UA_MOBILE if args.mobile else UA_DESKTOP
    try:
        resp = fetch(args.url, ua, args.timeout)
    except Exception as e:
        sys.exit(f"fetch failed: {type(e).__name__}: {e}")

    page = Page()
    page.feed(resp["html"])
    out = analyse(args.url, page, resp, args)
    if args.assets:
        out = add_assets(out, args.url, page, ua)

    text = json.dumps(out, indent=2)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
        summarise(out, args.out)
    else:
        print(text)


def summarise(out, path):
    m = out
    print(f"wrote {path}")
    print(f"  {m['page']['status']}  {m['page']['final_url']}")
    print(f"  h1: {m['hero']['h1']!r}")
    if m["match"]["score"] is not None:
        print(f"  message match: {m['match']['score']:.0%}"
              f"  missing: {', '.join(m['match']['missing_terms']) or 'none'}")
    else:
        print("  message match: NOT RUN (no --source-copy)")
    f = m["form"]
    print(f"  forms: {f['count']}  fields: {f['field_count']} "
          f"({f['required_count']} required)  submit: {f['submit_label']!r}")
    mo = m["mobile"]
    print(f"  input type errors: {mo['input_type_errors']}   "
          f"autocomplete missing: {mo['autocomplete_missing']}   "
          f"unlabelled: {mo['fields_without_label']}")
    a = m["attention"]
    print(f"  attention ratio: {a['links']} links / {a['goals']} goal(s) = {a['ratio']}")
    print(f"  price on page: {m['price']['on_page']}   "
          f"trial stated: {m['price']['trial_stated']}   "
          f"card requirement stated: {m['price']['card_required_stated']}")
    t = m["trust"]
    print(f"  trust markers: {', '.join(t['markers']) or 'none'}"
          f"   in form: {', '.join(t['in_form_container']) or 'NONE'}"
          + ("   (footer only)" if t["footer_only"] else ""))
    if m["page"]["likely_js_rendered"]:
        print("  !! almost no text without JavaScript -- use the browser layer")
    print("  rendered values (fold, occlusion, tap targets, contrast) still null "
          "-- merge them in from the browser")


if __name__ == "__main__":
    main()
