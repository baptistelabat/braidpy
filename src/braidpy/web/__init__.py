# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Package: braidpy.web
Description: Braids as plain data, for a page to draw
Authors: Baptiste Labat
Created: 2026-10-04
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

The braidpy web page runs braidpy itself, in the browser, through Pyodide,
and draws what it computes with three.js.  This package is everything the
page asks of braidpy: what can be made (:func:`catalogue`), and the braid a
description makes (:func:`build`), both as plain JSON-ready data — lists,
numbers and strings — so the page needs nothing of Python's to draw it.

A description says where the braid comes from — by default, the first
source offered:

``{"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6}``
    A braid word: signed generator indices (``1 -2``), ``s1 s2^-1``, or
    letters (``aB``, ``a`` for σ₁ and ``A`` its inverse).  With ``"layout":
    "ring"``, a ring word, the strands round a circle: ``n`` crosses the
    last strand and the first, across the seam, and ``n + 1`` turns them
    all one place round.
``{"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 8}``
    Kumihimo's own moves: swap top and bottom, rotate a quarter.
``{"source": "mobidai", "name": "KONGO_8", "cycles": 8}``
    A disk braid from the catalogue (:mod:`braidpy.mobidai_catalog`).
``{"source": "sinnet", "name": "abok_3042", "cycles": 4}``
    An Ashley solid sinnet (:mod:`braidpy.solid_sinnets_catalog`).
``{"source": "machine", "name": "tubular_8", "cycles": 3}``
    A horn gear braiding machine (:mod:`braidpy.horn_gear.examples`).

Every description may also give ``yarn_diameter`` and ``iterations``, the
tightening steps; 0 lays the yarns without tightening them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from braidpy.web import disks, machines, words
from braidpy.web._result import _PAGE_TIGHTENS, _TIGHTENING, recoloured
from braidpy.web._settings import COLOURS, OWN
from braidpy.web._spec import parse_moves, parse_word
from braidpy.web._types import MachineGeometry, MachineTurned, Result, Source, Spec
from braidpy.web.machines import machine_geometry, machine_origin, machine_turned

__all__ = [
    "MachineGeometry",
    "MachineTurned",
    "Result",
    "Source",
    "Spec",
    "build",
    "catalogue",
    "machine_geometry",
    "machine_origin",
    "machine_turned",
    "parse_moves",
    "parse_word",
    "premade",
    "premade_specs",
]

# What can be made, in the order the page offers it: each source's
# catalogue entry, and what builds it.
_SOURCES = {**words.SOURCES, **disks.SOURCES, **machines.SOURCES}


def catalogue() -> dict[str, Source]:
    """What the page can make, with sensible defaults for each source.

    Returns:
        Per source, a title, its defaults, and for the catalogued ones the
        entries to choose from, each with a name and a title.
    """
    return {source: entry() for source, (entry, _) in _SOURCES.items()}


def build(spec: Spec, tighten: bool = True) -> Result:
    """The braid a description makes, as data for a page to draw.

    Args:
        spec: The description; see the module's documentation.
        tighten: Tighten the yarns here.  If False they are only laid, and
            the result carries ``tighten``, everything a page needs to
            tighten them itself — as Braid Studio does, in JavaScript
            (``web/tighten.js``), many times faster than numpy in the
            browser: the samples' ``xy``, yarn after yarn, and
            :func:`~braidpy.take_off.tighten_yarns`'s settings; with
            ``chosen``, which of them the strands' points are, and
            ``centre``, what was taken off them.

    Returns:
        ``title``; ``strands``, each with its ``name``, ``colour`` and the
        ``points`` of its yarn's centreline, oldest first, the braid's axis
        along z; ``yarn_diameter``; ``info``, what is known of the braid —
        strands, its word and crossings, the permutation it makes; and
        ``notes`` worth telling whoever asked.  ``times`` says when each
        point was laid, and ``timeline`` what laid it, seen from above —
        the carriers' paths, the outlines under them and the slots — with
        its ``clock`` relating the source's time to the braid's.  A
        machine's axial cores are yarns among the others, named ``Core``.

    Raises:
        ValueError: If the description cannot be made.
    """
    source = spec.get("source", next(iter(_SOURCES)))
    if source not in _SOURCES:
        raise ValueError(f"Unknown source {source!r}: one of {sorted(_SOURCES)}.")
    later = _PAGE_TIGHTENS.set(not tighten)
    job = _TIGHTENING.set(None)
    try:
        return recoloured(_SOURCES[source][1](spec), COLOURS.read(spec))
    finally:
        _PAGE_TIGHTENS.reset(later)
        _TIGHTENING.reset(job)


def premade_specs() -> list[Spec]:
    """The braids a page offers as they come — each catalogued braid and
    each braid word example, with the source's defaults — to be made once,
    with the site, rather than by every visitor (:func:`premade`).

    Returns:
        Their descriptions, as short as they can be: what differs from the
        source's defaults is left to them.
    """
    specs: list[Spec] = []
    for source, about in catalogue().items():
        for entry in about.get("entries", []):
            if entry["name"] != OWN:
                specs.append(cast(Spec, {"source": source, "name": entry["name"]}))
        for example in about.get("examples", []):
            made = {k: v for k, v in example.items() if k != "title"}
            specs.append(cast(Spec, {"source": source, **made}))
    return specs


def _premade_one(spec: Spec) -> str | None:
    """One braid, laid for a page to tighten, as JSON; None if it cannot be
    made."""
    try:
        return json.dumps(build(spec, tighten=False), separators=(",", ":"))
    except ValueError:
        return None


def premade(directory: str, workers: int | None = None) -> list[dict[str, Any]]:
    """Make every braid of :func:`premade_specs`, laid as
    :func:`build` lays it for a page to tighten (``tighten=False``), and
    write each as JSON in ``directory``, with ``index.json`` saying which
    is which.  A page finding the braid asked for there shows it at once,
    without Python.  The same braid every time: unchanged, a file is
    written the same.

    Args:
        directory: Where to write them; made if missing.
        workers: Processes to make them with; one per processor if None.

    Returns:
        The index: per braid, its ``spec`` and its ``file``.
    """
    from concurrent.futures import ProcessPoolExecutor

    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    specs = premade_specs()
    index: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for number, (spec, text) in enumerate(
            zip(specs, pool.map(_premade_one, specs))
        ):
            if text is None:
                continue
            file = f"{number}.json"
            (out / file).write_text(text)
            index.append({"spec": spec, "file": file})
    (out / "index.json").write_text(json.dumps(index))
    return index
