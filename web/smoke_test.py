# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Open the built Braid Studio in a browser and make a braid of every kind.

Serves ``web/site`` locally, opens it in headless Chromium through
Playwright, and for each source checks that braidpy, running in the page,
made the braid and every yarn was drawn — with nothing logged as an error;
for the plait, that the card says what else makes it, and how to make it
on a disk or a lace machine; and for a machine,
that its handle turns it a step.

    python web/build.py
    python web/smoke_test.py                       # Pyodide from its CDN
    python web/smoke_test.py --pyodide /pyodide/   # or from the site itself

Needs ``pip install playwright`` and ``playwright install chromium``.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote, urlencode

SITE = Path(__file__).resolve().parent / "site"

# Small braids of every kind, and how many yarns each should draw.
CASES = [
    ({"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 3}, 3),
    ({"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2}, 8),
    ({"source": "mobidai", "name": "KONGO_8", "cycles": 2}, 8),
    ({"source": "sinnet", "name": "abok_3042", "cycles": 1}, 8),
    ({"source": "machine", "name": "tubular_8", "cycles": 1}, 8),
    # Laid on its fell ring, a machine's braid can be settled by physics.
    ({"source": "machine", "name": "flat_3", "cycles": 1, "settle": "physics"}, 3),
    # A lace machine, its card turning the gears; its handle too.
    ({"source": "lace", "name": "lace_plait", "cycles": 2}, 3),
    # And a card of your own: every gear turning on a ring of 6.
    (
        {
            "source": "lace",
            "name": "custom",
            "n_gears": 6,
            "card": "101010 010101",
            "cycles": 1,
        },
        6,
    ),
    (
        {
            "source": "sinnet",
            "name": "custom",
            "counts": "2 1 2 1 2 1",
            "moves": "1>5, 4>2, 5>3, 2>6, 3>1, 6>4",
            "cycles": 1,
        },
        9,
    ),
]

# The plait, as a braid word and on its machine: each also made as the other.
ALSO_MADE = [("word", "1 -2"), ("name", "flat_3")]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _serve(site: Path) -> socketserver.TCPServer:
    handler = functools.partial(_Quiet, directory=str(site))
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pyodide", help="Where Pyodide is; its CDN if not given.")
    parser.add_argument("--chromium", help="A Chromium to use instead of Playwright's.")
    parser.add_argument("--screenshots", type=Path, help="Save a picture of each.")
    parser.add_argument("--timeout", type=float, default=300, help="Seconds per page.")
    args = parser.parse_args()

    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    server = _serve(SITE)
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    query = f"?pyodide={quote(args.pyodide)}" if args.pyodide else ""
    failures = 0
    with sync_playwright() as playwright:
        launch = {"args": ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"]}
        if args.chromium:
            launch["executable_path"] = args.chromium
        browser = playwright.chromium.launch(**launch)
        for spec, n_yarns in CASES:
            page = browser.new_page(viewport={"width": 1200, "height": 800})
            errors: list[str] = []
            # Each page's errors to its own list.
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.on(
                "console",
                lambda message, errors=errors: (
                    errors.append(message.text) if message.type == "error" else None
                ),
            )
            started = time.time()
            page.goto(base + query + "#" + urlencode(spec))
            page.wait_for_function(
                "() => { const s = document.getElementById('status');"
                " return s.textContent.startsWith('Made') ||"
                " s.classList.contains('error'); }",
                timeout=args.timeout * 1000,
            )
            status = page.text_content("#status")
            drawn = page.evaluate("window.braidStudio.drawn")
            ok = status.startswith("Made") and drawn == n_yarns and not errors
            # Settled as asked, not fallen back to sideways.
            if spec.get("settle") == "physics":
                ok = ok and "Settled by physics" in page.inner_text("body")
            # A machine's handle turns it a step.
            if spec["source"] in ("machine", "lace"):
                try:
                    forward = ".handle button[title='Turn the handle a step']"
                    page.wait_for_selector(forward + ":not([disabled])", timeout=30000)
                    page.click(forward)
                    page.wait_for_function(
                        "() => document.querySelector('.handle .step')"
                        ".textContent === 'Step 1'",
                        timeout=30000,
                    )
                except PlaywrightTimeout:
                    ok = False
                    errors.append("the machine's handle did not turn")
            # Two strands coloured at once are a group, recoloured together.
            if spec["source"] == "word":
                try:
                    page.click("#strand-list button[data-strand='0']")
                    page.click(
                        "#strand-list button[data-strand='1']", modifiers=["Shift"]
                    )
                    page.click("#strand-palette .dab[data-colour='#000000']")
                    group = "#strand-groups button[data-strands='0,1']"
                    page.wait_for_selector(group, timeout=10000)
                    page.click(group)
                    page.click("#strand-palette .dab[data-colour='#ffffff']")
                    page.wait_for_function(
                        "() => ['0', '1'].every((i) => document.querySelector("
                        "`#strand-list button[data-strand='${i}']`)"
                        ".style.getPropertyValue('--swatch') === '#ffffff')",
                        timeout=10000,
                    )
                except PlaywrightTimeout:
                    ok = False
                    errors.append("a group of strands was not recoloured together")
            # Its kin, found in the page from the catalogue made with it.
            kin = ""
            if any(spec.get(key) == value for key, value in ALSO_MADE):
                try:
                    page.wait_for_function(
                        "() => document.getElementById('kin')"
                        ".textContent.includes('Also made as')",
                        timeout=30000,
                    )
                    kin = "  also made as others"
                except PlaywrightTimeout:
                    ok, kin = False, "  no kin shown"
                # And the braid made other ways: a disk, a lace card.
                try:
                    page.wait_for_function(
                        "() => document.getElementById('bridges')"
                        ".textContent.includes('Lace machine')",
                        timeout=30000,
                    )
                except PlaywrightTimeout:
                    ok, kin = False, kin + ", no other ways to make it shown"
            failures += not ok
            print(
                f"{'ok  ' if ok else 'FAIL'} {spec['source']:9} "
                f"{time.time() - started:5.1f}s  {status}  "
                f"{drawn} of {n_yarns} yarns drawn{kin}"
                + (f"  errors: {errors}" if errors else "")
            )
            if args.screenshots:
                args.screenshots.mkdir(parents=True, exist_ok=True)
                page.wait_for_timeout(500)
                name = str(spec["source"]) + (
                    "_custom" if spec.get("name") == "custom" else ""
                )
                page.screenshot(path=args.screenshots / f"{name}.png")
            page.close()
        browser.close()
    server.shutdown()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
