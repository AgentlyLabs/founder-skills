#!/usr/bin/env python3
"""Render an HTML deck to a 16:9 PDF, and optionally to per-slide PNGs.

Uses headless Chrome and nothing else, so there is no dependency to install
beyond a browser that is almost certainly already present.

    python3 build_deck.py deck.html --out deck.pdf
    python3 build_deck.py deck.html --out deck.pdf --png slides/

The PDF is vector with selectable text. PNGs render at 2x (3200x1800) for
social posts and embeds.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

CANVAS_W, CANVAS_H = 1600, 900

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge",
]


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    sys.exit("error: no Chrome/Chromium/Edge found. Install one, or pass --chrome PATH.")


def run_chrome(chrome: str, args: list) -> None:
    """Invoke Chrome headless, tolerating its noisy but harmless stderr."""
    proc = subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check", "--virtual-time-budget=10000", *args],
        capture_output=True, text=True,
    )
    # Chrome exits 0 while writing allocator/task_policy warnings to stderr, so
    # only surface stderr when it actually failed.
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        sys.exit(f"error: chrome exited {proc.returncode}")


class SlideSplitter(HTMLParser):
    """Split a deck into its top-level `.slide` elements.

    Regex would break on nested divs, which every real slide has. This tracks
    depth so it closes each slide at the right tag.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.head = []
        self.slides = []
        self._in_head = False
        self._depth = 0
        self._buf = None

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        if tag == "head":
            self._in_head = True
            return
        classes = dict(attrs).get("class", "") or ""
        if self._buf is None and tag == "div" and "slide" in classes.split():
            self._buf = [raw]
            self._depth = 1
            return
        if self._buf is not None:
            self._buf.append(raw)
            if tag == "div":
                self._depth += 1
        elif self._in_head:
            self.head.append(raw)

    def handle_startendtag(self, tag, attrs):
        raw = self.get_starttag_text()
        (self._buf if self._buf is not None else self.head if self._in_head else []).append(raw)

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
            return
        if self._buf is not None:
            if tag == "div":
                self._depth -= 1
                if self._depth == 0:
                    self._buf.append("</div>")
                    self.slides.append("".join(self._buf))
                    self._buf = None
                    return
            self._buf.append(f"</{tag}>")
        elif self._in_head:
            self.head.append(f"</{tag}>")

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)
        elif self._in_head:
            self.head.append(data)

    def handle_comment(self, data):
        if self._buf is not None:
            self._buf.append(f"<!--{data}-->")

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def export_pngs(chrome: str, src: str, outdir: str) -> int:
    with open(src, "r", encoding="utf-8") as handle:
        html = handle.read()

    splitter = SlideSplitter()
    splitter.feed(html)
    if not splitter.slides:
        sys.exit("error: found no top-level elements with class 'slide'")

    os.makedirs(outdir, exist_ok=True)
    head = "".join(splitter.head)
    # Temp files live beside the source so relative CSS/image paths still resolve.
    workdir = os.path.dirname(os.path.abspath(src)) or "."

    for index, slide in enumerate(splitter.slides, start=1):
        fd, tmp = tempfile.mkstemp(suffix=".html", prefix=f".slide{index:02d}_", dir=workdir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(f"<!doctype html><html><head>{head}</head><body>{slide}</body></html>")
            target = os.path.join(outdir, f"slide-{index:02d}.png")
            run_chrome(chrome, [
                "--force-device-scale-factor=2",
                f"--window-size={CANVAS_W},{CANVAS_H}",
                f"--screenshot={os.path.abspath(target)}",
                f"file://{os.path.abspath(tmp)}",
            ])
        finally:
            os.unlink(tmp)

    return len(splitter.slides)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render an HTML deck to PDF and PNGs.")
    parser.add_argument("html", help="Deck HTML file")
    parser.add_argument("--out", default="deck.pdf", help="Output PDF path (default: deck.pdf)")
    parser.add_argument("--png", metavar="DIR", help="Also export per-slide PNGs at 2x into DIR")
    parser.add_argument("--chrome", help="Path to a Chrome/Chromium binary")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.html):
        sys.exit(f"error: no such file: {args.html}")

    chrome = args.chrome or find_chrome()
    src = os.path.abspath(args.html)

    run_chrome(chrome, [
        "--no-pdf-header-footer",
        f"--print-to-pdf={os.path.abspath(args.out)}",
        f"file://{src}",
    ])
    if not os.path.isfile(args.out):
        sys.exit("error: chrome reported success but wrote no PDF")
    print(f"PDF  {args.out}  ({os.path.getsize(args.out)/1024:.0f} KB)")

    if args.png:
        count = export_pngs(chrome, src, args.png)
        print(f"PNG  {count} slides at {CANVAS_W*2}x{CANVAS_H*2} in {args.png}/")

    print("\nOpen the output and look at it before delivering. Headless rendering "
          "diverges from what the markup implies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
