# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Open the machine console in a browser and work the machine through it.

Serves ``web/site``, opens the console in headless Chromium, and checks the
things a person would: that the machine is drawn, that clicking a slot adds
and removes a carrier, that the handle turns both ways, and that a loading
which must collide stops the run and is ringed.

    python web/build.py
    python web/console_smoke_test.py

Needs ``pip install playwright`` and ``playwright install chromium``.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
READY = 180_000  # Pyodide and the wheels take a while on a cold cache


def serve(directory: Path):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyodide", default=None)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    if not (SITE / "console.html").exists():
        print("run web/build.py first", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    httpd, port = serve(SITE)
    url = f"http://127.0.0.1:{port}/console.html"
    if args.pyodide:
        url += f"?pyodide={args.pyodide}"

    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        page.on("pageerror", lambda e: problems.append(f"page error: {e}"))
        page.on(
            "console",
            lambda m: problems.append(f"console {m.type}: {m.text}")
            if m.type == "error"
            else None,
        )
        page.goto(url)

        # the machine is drawn once braidpy has loaded and answered
        page.wait_for_selector("#view circle.slot", timeout=READY)
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) > 0",
            timeout=READY,
        )
        slots = page.locator("#view circle.slot").count()
        carried = int(page.locator("#count").text_content())
        print(f"drawn: {slots} empty slots, {carried} carriers")
        if slots == 0 or carried == 0:
            problems.append("the machine was not drawn")

        # clicking an empty slot puts a carrier on it, clicking it again lifts it.
        # Slots meeting at a contact sit on top of one another, so click past
        # whatever is in front rather than hunt for a clear one.
        def slot(gear, index):
            return page.locator(
                f'#view circle[data-gear="{gear}"][data-slot="{index}"]'
            )

        def count():
            return int(page.locator("#count").text_content())

        page.locator("#clear").click()
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 0",
            timeout=30_000,
        )
        slot("G7", 0).click(force=True)
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 1",
            timeout=30_000,
        )
        slot("G7", 0).click(force=True)
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 0",
            timeout=30_000,
        )
        print("clicking a slot adds a carrier, clicking it again takes it off")

        # the handle turns forward and back
        slot("G7", 0).click(force=True)
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 1",
            timeout=30_000,
        )
        page.locator("#forward").click()
        page.wait_for_function(
            "() => document.getElementById('step').textContent === '1'",
            timeout=30_000,
        )
        page.locator("#back").click()
        page.wait_for_function(
            "() => document.getElementById('step').textContent === '0'",
            timeout=30_000,
        )
        print("the handle turns both ways")

        # two carriers either side of a contact are already on the same point,
        # so the page should ring them without the machine moving at all
        page.locator("#clear").click()
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 0",
            timeout=30_000,
        )
        slot("G0", 0).click(force=True)
        slot("G1", 0).click(force=True)
        page.wait_for_function(
            "() => document.querySelector('#view circle.clash') !== null",
            timeout=30_000,
        )
        ringed = page.locator("#view circle.clash").count()
        print(f"a bad placement is ringed at once ({ringed} rings)")
        if ringed < 2:
            problems.append("both carriers in a collision should be ringed")

        # and taking one off clears it
        slot("G1", 0).click(force=True)
        page.wait_for_function(
            "() => document.querySelector('#view circle.clash') === null",
            timeout=30_000,
        )
        print("taking one of them off clears the warning")

        # an empty machine must still show its gears turning: the slots sweep
        # through intermediate poses rather than jumping from step to step
        page.locator("#clear").click()
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) === 0",
            timeout=30_000,
        )
        poses = page.evaluate(
            """async () => {
              const pick = () => document.querySelector(
                '#view circle[data-gear="G7"][data-slot="0"]');
              const seen = [];
              const take = () => {
                const c = pick();
                if (c) seen.push(Number(c.getAttribute('cx')).toFixed(4));
              };
              take();
              const timer = setInterval(take, 20);
              document.getElementById('forward').click();
              await new Promise((r) => setTimeout(r, 900));
              clearInterval(timer);
              return [...new Set(seen)];
            }"""
        )
        print(f"an empty machine sweeps through {len(poses)} poses in one step")
        if len(poses) < 3:
            problems.append(
                f"a step should sweep through poses, saw {len(poses)}: {poses}"
            )

        # Run keeps turning the handle by itself, and stops when told
        page.locator("#reload").click()
        page.wait_for_function(
            "() => Number(document.getElementById('count').textContent) > 0",
            timeout=30_000,
        )
        page.locator("#rewind").click()
        page.wait_for_function(
            "() => document.getElementById('step').textContent === '0'",
            timeout=30_000,
        )
        page.locator("#play").click()
        page.wait_for_function(
            "() => Number(document.getElementById('step').textContent) >= 3",
            timeout=60_000,
        )
        page.locator("#play").click()  # stop
        page.wait_for_timeout(800)
        settled = page.locator("#step").text_content()
        page.wait_for_timeout(800)
        if page.locator("#step").text_content() != settled:
            problems.append("Run did not stop when asked")
        print(f"Run turns the handle on its own and stops when told (step {settled})")

        browser.close()
    httpd.shutdown()

    if problems:
        print("\nproblems:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("\nconsole smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
