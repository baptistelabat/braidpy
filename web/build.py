# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Assemble Braid Studio as a static site.

The page is plain files: the page itself, three.js, and braidpy as a wheel
for Pyodide to install in the browser — with math_braid, which braidpy
needs and PyPI has only as a source package.  Pyodide itself is loaded from
its CDN, or from wherever ``?pyodide=`` says.

Run from the repository root, after ``npm install`` in ``web/``::

    python web/build.py            # writes web/site/
    python -m http.server -d web/site

"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
PAGE = ["index.html", "style.css", "app.js", "worker.js"]
THREE = WEB / "node_modules" / "three"
MATH_BRAID = "math-braid==0.8"


def _wheel(source: str | Path, out: Path) -> Path:
    """Build one wheel of ``source`` — a directory or a source package."""
    before = set(out.glob("*.whl"))
    if shutil.which("uv"):
        command = ["uv", "build", "--wheel", "-o", str(out), str(source)]
    else:
        command = [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(out)]
        command.append(str(source))
    subprocess.run(command, check=True, cwd=ROOT)
    made = set(out.glob("*.whl")) - before
    if len(made) != 1:
        raise RuntimeError(f"Expected one wheel from {source}, got {made}.")
    return made.pop()


def _math_braid_sdist(into: Path) -> Path:
    """math_braid's source package, from PyPI: it has no wheel there."""
    name, version = MATH_BRAID.split("==")
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json") as r:
        release = json.load(r)
    (url,) = [f["url"] for f in release["urls"] if f["packagetype"] == "sdist"]
    sdist = into / url.rsplit("/", 1)[1]
    with urllib.request.urlopen(url) as r:
        sdist.write_bytes(r.read())
    return sdist


def build(site: Path) -> None:
    if not (THREE / "build" / "three.module.js").exists():
        raise SystemExit("three.js is missing: run `npm install` in web/ first.")
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)

    for name in PAGE:
        shutil.copy2(WEB / name, site / name)
    vendor = site / "vendor" / "three"
    (vendor / "addons" / "controls").mkdir(parents=True)
    shutil.copy2(THREE / "build" / "three.module.js", vendor / "three.module.js")
    (vendor / "addons" / "exporters").mkdir(parents=True)
    for addon in [
        "controls/OrbitControls.js",
        "exporters/STLExporter.js",
        "exporters/OBJExporter.js",
    ]:
        shutil.copy2(THREE / "examples" / "jsm" / addon, vendor / "addons" / addon)
    shutil.copy2(THREE / "LICENSE", vendor / "LICENSE")

    wheels = site / "wheels"
    wheels.mkdir()
    braidpy = _wheel(ROOT, wheels)
    with tempfile.TemporaryDirectory() as scratch:
        math_braid = _wheel(_math_braid_sdist(Path(scratch)), wheels)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    (wheels / "manifest.json").write_text(
        json.dumps(
            {"version": version, "wheels": [math_braid.name, braidpy.name]},
            indent=2,
        )
    )
    # GitHub Pages: serve the files as they are.
    (site / ".nojekyll").write_text("")
    print(f"Braid Studio written to {site}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out", type=Path, default=WEB / "site", help="Where to write the site."
    )
    build(parser.parse_args().out)


if __name__ == "__main__":
    main()
