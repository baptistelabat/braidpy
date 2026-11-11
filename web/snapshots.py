# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Take a picture of every braid the front page lists, settled, as the
studio shows it.

Each braid of braids.json is opened in the built studio (make.html), in a
headless browser; made with the site, it is shown settled at once.  The 3D
view is then drawn into a small picture, kept beside the site as
snapshots/<key>.webp, for the front page's table (home.js).

    python web/build.py && python web/snapshots.py

It needs a browser, as web/smoke_test.py does; a site built without one
has no pictures, and its front page shows none.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from urllib.parse import quote, urlencode

from smoke_test import SITE, _serve

# The picture, in pixels: twice the front page's 96 × 128, for sharp screens.
WIDTH, HEIGHT = 192, 256
# The browser's window: the studio's panel beside a view of the picture's
# shape, big enough to draw it well.
PANEL = 360
VIEW_SCALE = 3
# How good the pictures are, 0 to 1: small files, the eye sees no loss.
QUALITY = 0.8

# The view, drawn into a picture of its own, its middle kept: what the
# studio frames is in the middle.
_DRAWN = """([width, height, quality]) => {
  const view = document.querySelector('#viewer canvas');
  const picture = document.createElement('canvas');
  picture.width = width;
  picture.height = height;
  const scale = Math.max(width / view.width, height / view.height);
  const w = view.width * scale, h = view.height * scale;
  picture.getContext('2d').drawImage(view, (width - w) / 2, (height - h) / 2, w, h);
  return picture.toDataURL('image/webp', quality);
}"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pyodide", help="Where Pyodide is; its CDN if not given.")
    parser.add_argument("--chromium", help="A Chromium to use instead of Playwright's.")
    parser.add_argument("--timeout", type=float, default=120, help="Seconds per braid.")
    args = parser.parse_args()

    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    braids = json.loads((SITE / "braids.json").read_text())
    out = SITE / "snapshots"
    out.mkdir(exist_ok=True)
    server = _serve(SITE)
    base = f"http://127.0.0.1:{server.server_address[1]}/make.html"
    query = f"?pyodide={quote(args.pyodide)}" if args.pyodide else ""
    missed = []
    with sync_playwright() as playwright:
        launch = {"args": ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"]}
        if args.chromium:
            launch["executable_path"] = args.chromium
        browser = playwright.chromium.launch(**launch)
        # One context for them all: Pyodide and the page are fetched once.
        context = browser.new_context(
            viewport={
                "width": PANEL + WIDTH * VIEW_SCALE // 2,
                "height": HEIGHT * VIEW_SCALE // 2,
            }
        )
        for braid in braids:
            started = time.time()
            page = context.new_page()
            try:
                page.goto(base + query + "#" + urlencode(braid["spec"]))
                page.wait_for_function(
                    "() => window.braidStudio?.result?.settled",
                    timeout=args.timeout * 1000,
                )
                # Drawn once more, settled, before it is read.
                page.wait_for_timeout(500)
                data = page.evaluate(_DRAWN, [WIDTH, HEIGHT, QUALITY])
                picture = base64.b64decode(data.split(",", 1)[1])
                (out / f"{braid['key']}.webp").write_bytes(picture)
                print(
                    f"ok   {braid['key']:40} {time.time() - started:5.1f}s "
                    f"{len(picture) / 1000:5.1f} kB"
                )
            except PlaywrightTimeout:
                missed.append(braid["key"])
                print(f"MISS {braid['key']:40} not settled in {args.timeout:.0f}s")
            page.close()
        browser.close()
    server.shutdown()
    print(f"{len(braids) - len(missed)} of {len(braids)} braids pictured")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
