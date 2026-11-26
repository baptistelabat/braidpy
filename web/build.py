# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Assemble Braid Studio as a static site.

The page is plain files: the page itself, three.js, and braidpy as a wheel
for Pyodide to install in the browser.  Pyodide itself is loaded from
its CDN, or from wherever ``?pyodide=`` says.  With them, what braidpy
would otherwise say in every browser, said here once: what the page can
make, so that its form is filled before Python has started, and the
catalogue of braids by topology (:mod:`braidpy.topology_catalog`), some ten
seconds here, minutes there.

Run from the repository root, after ``npm install`` in ``web/``::

    python web/build.py            # writes web/site/
    python -m http.server -d web/site

"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: tomllib's forerunner
    import tomli as tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
# The page's settling, run by Node on the braids made with the site
# (settle_node.js): what it runs, and where what it made is kept between
# builds, by what went in.
SETTLING = [
    "settle_node.js",
    "settle.js",
    "tighten.js",
    "rope.js",
    "form.js",
    "carried.js",
    "marudai.js",
    "b3d.js",
    "frames.js",
]
SETTLED_CACHE = Path(os.environ.get("BRAID_STUDIO_SETTLED", WEB / ".settled"))
# How hard the braids made with the site are gzipped (_compressed): the most,
# as it costs only the build; a browser unpacks any level as fast.
GZIP_LEVEL = 9
PAGE = [
    # The front page: the braids to look up, each to open in the studio.
    "index.html",
    "home.js",
    # The studio.
    "make.html",
    "style.css",
    # The page, in modules (app.js says what each is).
    "app.js",
    "page.js",
    "fields.js",
    "diagram.js",
    "machine.js",
    "editor.js",
    "spec.js",
    "workers.js",
    "defaults.js",
    "scene.js",
    "frames.js",
    "insets.js",
    "info.js",
    "colours.js",
    "controls.js",
    "i18n.js",
    # Its workers, and what they load.
    "worker.js",
    "settle.js",
    "tighten.js",
    "rope.js",
    "form.js",
    "carried.js",
    "marudai.js",
    "b3d.js",
]
# What the site calls itself, whom it credits and where it links: this
# repository's Braid Studio, unless another profile is given (--profile).
PROFILE = WEB / "profile.toml"
# Each language's words, by their English (web/i18n.js), every one offered
# by the page's menu.
LOCALES = WEB / "locales"
THREE = WEB / "node_modules" / "three"


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


# A page file named in another, in double quotes, as a module's imports, a
# worker, importScripts and the page's stylesheet and script name them:
# "name.js", "./name.js".
_NAMED = re.compile(r'"(\./)?([\w.-]+\.(?:js|css))"')
# A page's parts kept only when a key of the profile is set (or, with
# "not", only when it is not): a whole line or more, markers on lines of
# their own, or a few words.
_IF = r"<!-- if (not )?(\w+) -->"
_END = r"<!-- end if -->"
_LINES = re.compile(rf"^[ \t]*{_IF}\n(.*?)^[ \t]*{_END}\n", re.MULTILINE | re.DOTALL)
_WORDS = re.compile(rf"{_IF}(.*?){_END}", re.DOTALL)
_FILLED = re.compile(r"\{\{(\w+)\}\}")


def profile(path: Path = PROFILE) -> dict[str, Any]:
    """A site's profile: what it calls itself, whom it credits and where it
    links.  It gives every key this repository's own profile gives, and no
    other: a site built from braidpy decides each, a key added here
    included, rather than taking this one's.  Its ``packages``, given from
    where the profile is, come back as absolute paths."""
    given = tomllib.loads(path.read_text())
    expected = tomllib.loads(PROFILE.read_text())
    if given.keys() != expected.keys():
        raise SystemExit(
            f"{path} gives {sorted(given)}; a profile gives {sorted(expected)}."
        )
    given["packages"] = [str((path.parent / p).resolve()) for p in given["packages"]]
    return given


def _rendered(text: str, site: dict[str, Any]) -> str:
    """A page filled with its site's profile: ``{{key}}`` by its value, a
    part kept or left out as its key is set or not."""

    def value(key: str) -> Any:
        if key not in site:
            raise RuntimeError(f"The page asks for {key!r}, which no profile gives.")
        return site[key]

    def kept(block: re.Match) -> str:
        negated, key, body = block.groups()
        return body if bool(value(key)) != bool(negated) else ""

    def filled(named: re.Match) -> str:
        escaped = html.escape(str(value(named.group(1))), quote=False)
        return escaped.replace('"', "&quot;")

    return _FILLED.sub(filled, _WORDS.sub(kept, _LINES.sub(kept, text)))


def locale(language: str, packages: Sequence[str] = ()) -> str:
    """The page's words in every language of ``web/locales/`` (web/i18n.js),
    as the module the page imports, opening in ``language``: each
    ``<code>.toml`` a text by its English; English needs none.  Each of the
    site's ``packages`` adds the words of its own braids from its own
    ``locales/``, kept out of braidpy's."""
    catalogues: dict[str, dict[str, str]] = {}
    for folder in [LOCALES, *(Path(p) / "locales" for p in packages)]:
        for source in sorted(folder.glob("*.toml")):
            catalogues.setdefault(source.stem, {}).update(
                tomllib.loads(source.read_text())
            )
    if language != "en" and language not in catalogues:
        raise SystemExit(f"No words in {language!r}: no {LOCALES}/{language}.toml.")
    return (
        "// The page's words in each language, written by web/build.py from\n"
        "// web/locales/: see web/i18n.js.\n"
        f"export const language = {json.dumps(language)};\n"
        f"export const catalogues = {json.dumps(catalogues, ensure_ascii=False, indent=0)};\n"
    )


def _copy_page(site: Path, about: dict[str, Any]) -> None:
    """The page's own files, each naming the others with the page's version,
    its HTML filled with the site's profile (``about``), and its words in
    the site's language (:func:`locale`).

    The version is a fingerprint of all of them: a browser holding an old
    copy of any file fetches the new one, and never mixes old modules with
    new ones.  Modules import each other both ways, so a file's own
    fingerprint could not go into the files that name it."""
    texts = {}
    for name in PAGE:
        text = (WEB / name).read_text()
        texts[name] = _rendered(text, about) if name.endswith(".html") else text
    texts["locale.js"] = locale(str(about["language"]), about["packages"])
    digest = hashlib.sha256()
    for name, text in texts.items():
        digest.update(name.encode() + b"\0" + text.encode())
    version = digest.hexdigest()[:10]

    def stamp(named: re.Match) -> str:
        here, name = named.groups()
        if name not in texts:
            return named.group(0)
        return f'"{here or ""}{name}?v={version}"'

    for name, text in texts.items():
        for module in re.findall(r'(?:from|import) "\./([^"]+)"', text):
            if module not in texts:
                raise RuntimeError(f"{name} imports {module}, which is not in PAGE.")
        # A worker's own scripts, too: those named outright, not a URL
        # put together.
        for loaded in re.findall(r"importScripts\(([^)]*)\)", text):
            for given in loaded.split(","):
                script = re.fullmatch(r'\s*"([^"]+)"\s*', given)
                if script and script.group(1) not in PAGE:
                    raise RuntimeError(
                        f"{name} loads {script.group(1)}, which is not in PAGE."
                    )
        (site / name).write_text(_NAMED.sub(stamp, text))


def _braidpy(script: str, packages: Sequence[str] = ()) -> subprocess.CompletedProcess:
    """A Python script run with braidpy and all it needs: the project's own
    environment, with the site's ``packages`` (without uv, installed in it
    already)."""
    if shutil.which("uv"):
        command = ["uv", "run", "--project", str(ROOT)]
        for package in packages:
            command += ["--with", package]
        command += ["python", "-c", script]
    else:
        command = [sys.executable, "-c", script]
    return subprocess.run(command, check=True, cwd=ROOT, capture_output=True, text=True)


def _premade(site: Path, packages: Sequence[str] = ()) -> None:
    """Every braid the page offers as it comes, made once here
    (``braidpy.web.premade``): a visitor choosing one sees it at once,
    without waiting for Python — the biggest sinnets took minutes."""
    script = f"from braidpy import web; web.premade({str(site / 'made')!r})"
    _braidpy(script, packages)


def _settled(site: Path, cache: Path = SETTLED_CACHE) -> None:
    """Every braid made with the site, settled as the page would settle it
    as it comes (settle_node.js runs the page's own settle.js): a visitor
    choosing one is shown it settled at once, rather than after a minute
    or more on the marudai.

    Settling them all takes some twenty minutes of a processor, so each is
    kept in ``cache`` by what went into it — the braid as laid, and the
    settling's code — and settled again only when either changes.  What is
    no longer asked for is cleared from the cache.  Without Node, the page
    settles them itself, as before.
    """
    from concurrent.futures import ThreadPoolExecutor

    if not shutil.which("node"):
        print("No Node: the braids made with the site are left for the page to settle.")
        return
    made = site / "made"
    code = hashlib.sha256(b"".join((WEB / name).read_bytes() for name in SETTLING))
    index = json.loads((made / "index.json").read_text())
    cache.mkdir(parents=True, exist_ok=True)

    def settle(entry: dict) -> None:
        laid = made / entry["file"]
        key = code.copy()
        key.update(laid.read_bytes())
        kept = cache / f"{key.hexdigest()}.json"
        if not kept.exists():
            fresh = kept.with_suffix(".part")
            done = subprocess.run(
                ["node", str(WEB / "settle_node.js"), str(laid), str(fresh)],
                check=False,
            )
            if done.returncode:
                # Left for the page to settle, as it would without Node.
                print(f"Not settled: {entry['spec']}")
                return
            fresh.replace(kept)
        entry["settled"] = laid.stem + ".settled.json"
        shutil.copyfile(kept, made / entry["settled"])
        entry["key"] = kept.name

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
        list(pool.map(settle, index))
    kept = {cache / e.pop("key") for e in index if "key" in e}
    for stale in set(cache.glob("*.json")) - kept:
        stale.unlink()
    (made / "index.json").write_text(json.dumps(index))


def _compressed(site: Path) -> None:
    """The braids made with the site, gzipped: a tenth of their size or less,
    and the site within what GitHub Pages will serve.  The page unpacks each
    as it fetches it (workers.js), natively.  Done last, so that what they
    are made and settled from, and the settled cache's keys, are the braids
    themselves; written the same every time, the same braid unchanged."""
    made = site / "made"
    index = json.loads((made / "index.json").read_text())
    for entry in index:
        for key in ("file", "settled"):
            if key not in entry:
                continue
            plain = made / entry[key]
            packed = plain.with_name(plain.name + ".gz")
            packed.write_bytes(gzip.compress(plain.read_bytes(), GZIP_LEVEL, mtime=0))
            plain.unlink()
            entry[key] = packed.name
    (made / "index.json").write_text(json.dumps(index))


def _data(site: Path, packages: Sequence[str] = ()) -> None:
    """What braidpy says once, for every visit, as JSON: the page's
    catalogue — what it can make, offered before Python has started — the
    catalogue of braids by topology, and the table of braids the front
    page lists (``braids.json``).  Made by braidpy with all it
    needs, in the project's own environment."""
    script = (
        "import json, sys; from braidpy import web; "
        "from braidpy.topology_catalog import export; "
        "topologies = export(); "
        "json.dump({'catalogue': web.catalogue(), 'topologies': topologies, "
        "'braids': web.braids(topologies)}, sys.stdout)"
    )
    data = json.loads(_braidpy(script, packages).stdout)
    for name, value in data.items():
        (site / f"{name}.json").write_text(json.dumps(value))


def build(site: Path, premade: bool = True, about: Path = PROFILE) -> None:
    if not (THREE / "build" / "three.module.js").exists():
        raise SystemExit("three.js is missing: run `npm install` in web/ first.")
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)

    described = profile(about)
    _copy_page(site, described)
    if not described["indexed"]:
        # Search engines read it only at a host's root: a site served there.
        (site / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    _data(site, described["packages"])
    if premade:
        _premade(site, described["packages"])
        _settled(site)
        _compressed(site)
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
    # The site's own packages, installed after braidpy, whose catalogues
    # they add to (braidpy.catalogue.extended).
    own = [_wheel(package, wheels) for package in described["packages"]]
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    (wheels / "manifest.json").write_text(
        json.dumps(
            {
                "version": version,
                "wheels": [braidpy.name, *(w.name for w in own)],
            },
            indent=2,
        )
    )
    # uv build leaves a .gitignore of "*" beside its wheels: published by
    # committing to gh-pages, they would be left out, and the page would
    # find no braidpy.
    for ignore in site.rglob(".gitignore"):
        ignore.unlink()
    # GitHub Pages: serve the files as they are.
    (site / ".nojekyll").write_text("")
    print(f"Braid Studio written to {site}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out", type=Path, default=WEB / "site", help="Where to write the site."
    )
    parser.add_argument(
        "--no-premade",
        action="store_true",
        help="Leave out the braids made with the site: quicker, for trying the page.",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=PROFILE,
        help="What the site calls itself, whom it credits and where it links.",
    )
    args = parser.parse_args()
    build(args.out, premade=not args.no_premade, about=args.profile)


if __name__ == "__main__":
    main()
