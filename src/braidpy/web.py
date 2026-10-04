# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: web.py
Description: Braids as plain data, for a page to draw
Authors: Baptiste Labat
Created: 2026-10-04
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

The braidpy web page runs braidpy itself, in the browser, through Pyodide,
and draws what it computes with three.js.  This module is everything the
page asks of braidpy: what can be made (:func:`catalogue`), and the braid a
description makes (:func:`build`), both as plain JSON-ready data — lists,
numbers and strings — so the page needs nothing of Python's to draw it.

A description says where the braid comes from:

``{"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6}``
    A braid word: signed generator indices (``1 -2``), ``s1 s2^-1``, or
    letters (``aB``, ``a`` for σ₁ and ``A`` its inverse).
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

import math
import re
from typing import Any, Callable, Dict, Hashable, List, Mapping, Optional, Sequence

import numpy as np

__all__ = ["build", "catalogue", "parse_word"]

# Points along a yarn are rounded to this many decimals: a tenth of a
# thousandth of a yarn is finer than any screen.
_DECIMALS = 4

# Above this many points along a yarn, the page gets one in so many.
_MAX_POINTS = 1500

# The same colours the horn gear animation gives its carriers.
_PALETTE = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
    "#f781bf",
    "#999999",
    "#66c2a5",
    "#fc8d62",
    "#8da0cb",
    "#e78ac3",
]


def parse_word(text: str) -> List[int]:
    """A braid word, as signed generator indices.

    Reads ``1 -2 1`` (or with commas), ``s1 s2^-1 s1`` (``σ`` too), and
    letters, ``aBa``: ``a`` is σ₁, ``b`` σ₂ and so on, a capital the inverse.

    Args:
        text: The word.

    Returns:
        The generators; empty for an empty word.

    Raises:
        ValueError: If the text is none of these.
    """
    text = text.strip()
    if not text:
        return []
    if re.fullmatch(r"[A-Za-z]+", text) and not re.search(r"[sσ]\d", text):
        return [
            (ord(c) - ord("a") + 1) if c.islower() else -(ord(c) - ord("A") + 1)
            for c in text
        ]
    word: List[int] = []
    for token in re.split(r"[\s,;.]+", text):
        if not token:
            continue
        plain = re.fullmatch(r"[+-]?\d+", token)
        if plain:
            word.append(int(token))
            continue
        named = re.fullmatch(r"[sσ](\d+)(\^?\(?(-?1)\)?)?", token)
        if named:
            index = int(named.group(1))
            word.append(-index if named.group(3) == "-1" else index)
            continue
        raise ValueError(f"Cannot read {token!r} as a generator.")
    if any(g == 0 for g in word):
        raise ValueError("Generators are numbered from 1.")
    return word


# ---------------------------------------------------------------- catalogue


def _machines() -> Dict[str, Callable[[], Any]]:
    from braidpy.horn_gear import examples

    return {
        "flat_3": examples.flat_braid_3,
        "flat_4": examples.flat_braid_4,
        "flat_9": examples.flat_braid_9,
        "soutache_5": examples.soutache_braid,
        "soutache_7": lambda: examples.soutache_braid(n_slots=7),
        "princess": examples.princess_braid,
        "tubular_8": examples.tubular_braid_8,
        "tubular_12": examples.tubular_braid_12,
        "tubular_16": examples.tubular_braid_16,
    }


_MACHINE_TITLES = {
    "flat_3": "Flat braid, 3 carriers",
    "flat_4": "Flat braid, 4 carriers",
    "flat_9": "Flat braid, 9 carriers on a single track",
    "soutache_5": "Soutache, 2 gears of 5",
    "soutache_7": "Soutache, 2 gears of 7",
    "princess": "Princess, 5/6/5 gears, 8 carriers",
    "tubular_8": "Tubular braid, 8 carriers",
    "tubular_12": "Tubular braid, 12 carriers",
    "tubular_16": "Tubular braid, 16 carriers",
}


def _sinnets() -> Dict[str, Any]:
    import braidpy.solid_sinnets_catalog as catalogue
    from braidpy.ashley_solid_sinnet import AshleySolidSinnet

    return {
        name: value
        for name, value in sorted(vars(catalogue).items())
        if isinstance(value, AshleySolidSinnet)
    }


def _mobidais() -> Dict[str, Any]:
    import braidpy.mobidai_catalog as catalogue
    from braidpy.mobidai_catalog import CataloguedBraid

    return {
        name: value
        for name, value in vars(catalogue).items()
        if isinstance(value, CataloguedBraid)
    }


def catalogue() -> Dict[str, Any]:
    """What the page can make, with sensible defaults for each source.

    Returns:
        Per source, a title, its defaults, and for the catalogued ones the
        entries to choose from, each with a name and a title.
    """
    sinnets = _sinnets()
    mobidais = _mobidais()
    return {
        "word": {
            "title": "Braid word",
            "defaults": {"word": "1 -2", "n_strands": 3, "repeat": 6},
            "examples": [
                {"word": "1 -2", "n_strands": 3, "repeat": 6, "title": "Plait"},
                {"word": "1 2 3", "n_strands": 4, "repeat": 4, "title": "Twist"},
                {
                    "word": "1 -2 3 -2",
                    "n_strands": 4,
                    "repeat": 4,
                    "title": "Four-strand flat",
                },
                {"word": "1 1 1", "n_strands": 2, "repeat": 2, "title": "Two-ply"},
            ],
        },
        "kumihimo": {
            "title": "Kumihimo (S/R moves)",
            "defaults": {"pattern": "SR", "n_strands": 8, "repeat": 8},
        },
        "mobidai": {
            "title": "Kumihimo disk (mobidai)",
            "defaults": {"name": "KONGO_8", "cycles": 6},
            "entries": [
                {
                    "name": key,
                    "title": f"{entry.name} ({entry.n_strands} strands)",
                }
                for key, entry in mobidais.items()
            ],
        },
        "sinnet": {
            "title": "Ashley solid sinnet",
            "defaults": {"name": "abok_3042", "cycles": 3},
            "entries": [
                {
                    "name": name,
                    "title": f"ABOK #{name.split('_')[1]} ({sinnet.n_strands} strands)",
                }
                for name, sinnet in sinnets.items()
            ],
        },
        "machine": {
            "title": "Horn gear braiding machine",
            "defaults": {"name": "tubular_8", "cycles": 2},
            "entries": [
                {"name": name, "title": title}
                for name, title in _MACHINE_TITLES.items()
            ],
        },
    }


# -------------------------------------------------------------------- build


def build(spec: Mapping[str, Any]) -> Dict[str, Any]:
    """The braid a description makes, as data for a page to draw.

    Args:
        spec: The description; see the module's documentation.

    Returns:
        ``title``; ``strands``, each with its ``name``, ``colour`` and the
        ``points`` of its yarn's centreline, oldest first, the braid's axis
        along z; ``yarn_diameter``; ``info``, what is known of the braid —
        strands, its word and crossings, the permutation it makes; and
        ``notes`` worth telling whoever asked.  A machine braiding round a
        core also gives its ``cores``, each a segment ``from`` and ``to``.

    Raises:
        ValueError: If the description cannot be made.
    """
    source = spec.get("source", "word")
    builders = {
        "word": _from_word,
        "kumihimo": _from_kumihimo,
        "mobidai": _from_mobidai,
        "sinnet": _from_sinnet,
        "machine": _from_machine,
    }
    if source not in builders:
        raise ValueError(f"Unknown source {source!r}: one of {sorted(builders)}.")
    return builders[source](spec)


def _number(spec: Mapping[str, Any], key: str, default: float, low: float, high: float):
    value = spec.get(key, default)
    if value is None or value == "":
        return default
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} should be a number, not {value!r}.") from None
    if not low <= value <= high:
        raise ValueError(f"{key} should be between {low:g} and {high:g}.")
    return value


def _count(spec: Mapping[str, Any], key: str, default: int, low: int, high: int) -> int:
    value = _number(spec, key, default, low, high)
    if value != int(value):
        raise ValueError(f"{key} should be a whole number.")
    return int(value)


def _tighten(paths, spec: Mapping[str, Any], diameter: float, default: int = 150):
    from braidpy.take_off import tighten_yarns

    iterations = _count(spec, "iterations", default, 0, 2000)
    if iterations == 0:
        return paths
    tightened, _ = tighten_yarns(paths, diameter, iterations=iterations)
    return tightened


def _tighten_round(paths, spec: Mapping[str, Any], diameter: float, core_radius):
    from braidpy.take_off import tighten_yarns

    # Kept outside the core, each step costs more: fewer of them by default.
    iterations = _count(spec, "iterations", 80, 0, 2000)
    if iterations == 0:
        return paths
    tightened, _ = tighten_yarns(
        paths, diameter, iterations=iterations, core_radius=core_radius
    )
    return tightened


def _result(
    title: str,
    paths,
    diameter: float,
    colours: Optional[Sequence[str]] = None,
    names: Optional[Sequence[str]] = None,
    info: Optional[Dict[str, Any]] = None,
    notes: Sequence[str] = (),
) -> Dict[str, Any]:
    """Everything the page draws, as plain data."""
    n = paths.formed_count
    keys: List[Hashable] = list(paths.points)
    stride = max(1, math.ceil(n / _MAX_POINTS))
    centre = np.array([paths.axis[0], paths.axis[1], 0.0])
    strands = []
    for i, key in enumerate(keys):
        points = np.asarray(paths.points[key][:n:stride], dtype=float) - centre
        if stride > 1 and (n - 1) % stride:
            points = np.vstack([points, paths.points[key][n - 1] - centre])
        if not np.all(np.isfinite(points)):
            raise ValueError("The braid could not be laid: its yarns ran off.")
        colour = colours[i % len(colours)] if colours else _PALETTE[i % len(_PALETTE)]
        name = names[i] if names else f"Strand {key}"
        strands.append(
            {
                "name": name,
                "colour": colour,
                "points": np.round(points, _DECIMALS).tolist(),
            }
        )
    out_info: Dict[str, Any] = {"n_strands": len(keys)}
    out_info.update(info or {})
    try:
        out_info["closest_approach"] = round(
            float(paths.closest_approach(include_fell=False)), _DECIMALS
        )
    except Exception:  # an estimate only; never worth failing the braid over
        pass
    return {
        "title": title,
        "strands": strands,
        "yarn_diameter": diameter,
        "info": out_info,
        "notes": list(notes),
    }


def _braid_info(word: Sequence[int], n_strands: int) -> Dict[str, Any]:
    """What is known of a flat braid word: its crossings and permutation."""
    from braidpy.braid import Braid

    word = [int(g) for g in word]
    info: Dict[str, Any] = {
        "word": " ".join(str(g) for g in word),
        "crossings": len(word),
        "exponent_sum": int(sum(np.sign(word))),
    }
    if word:
        braid = Braid(word, n_strands)
        info["permutation"] = [int(p) for p in braid.perm()]
        info["pure"] = bool(braid.is_pure())
    return info


def _from_word(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.braid import Braid
    from braidpy.take_off import braid_word_trajectories, lay_yarns

    word = parse_word(str(spec.get("word", "")))
    if not word:
        raise ValueError("Give a braid word, for example 1 -2.")
    repeat = _count(spec, "repeat", 1, 1, 50)
    needed = max(abs(g) for g in word) + 1
    n_strands = _count(spec, "n_strands", needed, 2, 32)
    if n_strands < needed:
        raise ValueError(f"σ{needed - 1} needs at least {needed} strands.")
    word = word * repeat
    if len(word) > 400:
        raise ValueError("That is over 400 crossings: repeat it fewer times.")
    diameter = _number(spec, "yarn_diameter", 0.45, 0.05, 0.95)
    trajectories = braid_word_trajectories(Braid(word, n_strands))
    paths = lay_yarns(trajectories, yarn_diameter=diameter, fell_radius=0.0)
    paths = _tighten(paths, spec, diameter)
    return _result(
        f"Braid word {spec.get('word', '')}"
        + (f", {repeat} times" if repeat > 1 else ""),
        paths,
        diameter,
        info=_braid_info(word, n_strands),
    )


def _disk_info(start, steps, n_slots: int, clockwise: bool) -> Dict[str, Any]:
    """A disk braid's word, read round the ring and with the middle solid."""
    from braidpy.annulus_braid import solid_word
    from braidpy.take_off import disk_annular_word

    annular, n = disk_annular_word(start, steps, n_slots, clockwise=clockwise)
    info = _braid_info(solid_word(annular, n), n)
    info["annular_word"] = " ".join(str(g) for g in annular)
    return info


def _from_kumihimo(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.take_off import disk_braid, kumihimo_steps

    pattern = re.sub(r"\s+", "", str(spec.get("pattern", "SR"))).upper()
    if not pattern or set(pattern) - {"S", "R"}:
        raise ValueError("A kumihimo pattern is made of S (swap) and R (rotate).")
    n_strands = _count(spec, "n_strands", 8, 4, 32)
    if n_strands % 4:
        raise ValueError("Kumihimo needs a multiple of 4 strands.")
    repeat = _count(spec, "repeat", 8, 1, 50)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    n_slots, start, steps = kumihimo_steps(pattern * repeat, n_strands)
    paths = disk_braid(
        start,
        steps,
        n_slots,
        diameter,
        iterations=_count(spec, "iterations", 200, 0, 2000),
        clockwise=False,
    )
    return _result(
        f"Kumihimo {pattern} × {repeat}, {n_strands} strands",
        paths,
        diameter,
        colours=_hues(n_strands),
        info=_disk_info(start, steps, n_slots, clockwise=False),
    )


def _from_mobidai(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.take_off import disk_braid, mobidai_steps

    mobidais = _mobidais()
    name = str(spec.get("name", "KONGO_8"))
    if name not in mobidais:
        raise ValueError(f"No mobidai braid {name!r}: one of {sorted(mobidais)}.")
    entry = mobidais[name]
    config = entry.to_config()
    cycles = _count(spec, "cycles", 6, 1, 40)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    start, steps = mobidai_steps(config, cycles)
    clockwise = getattr(config, "is_clockwise", True)
    paths = disk_braid(
        start,
        steps,
        config.n_slots,
        diameter,
        iterations=_count(spec, "iterations", 200, 0, 2000),
        clockwise=clockwise,
    )
    colours = [colour for _, colour in entry.initial_slots]
    return _result(
        f"{entry.name[0].upper()}{entry.name[1:]}, {cycles} cycles",
        paths,
        diameter,
        colours=colours,
        info=_disk_info(start, steps, config.n_slots, clockwise),
    )


def _from_sinnet(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.ashley_solid_sinnet import strand_colours

    sinnets = _sinnets()
    name = str(spec.get("name", "abok_3042"))
    if name not in sinnets:
        raise ValueError(f"No sinnet {name!r}: one of {sorted(sinnets)}.")
    sinnet = sinnets[name]
    cycles = _count(spec, "cycles", 3, 1, 12)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    paths = sinnet.braid_3d(
        diameter,
        n_cycles=cycles,
        iterations=_count(spec, "iterations", 200, 0, 2000),
    )
    disk = sinnet.disk(cycles)
    notes = []
    counts = list(sinnet.initial_counts_per_space)
    for source, target in sinnet.moves:
        counts[source - 1] -= 1
        counts[target - 1] += 1
    if counts != list(sinnet.initial_counts_per_space):
        notes.append(
            "Its moves do not bring every space back to its count after a "
            "cycle: the catalogue's moves may be mistranscribed."
        )
    return _result(
        f"ABOK #{name.split('_')[1]}, {sinnet.n_strands}-strand sinnet, "
        f"{cycles} cycles",
        paths,
        diameter,
        colours=strand_colours(sinnet.n_strands),
        info=_disk_info(disk.start, disk.steps, disk.n_slots, clockwise=False),
        notes=notes,
    )


def _from_machine(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.horn_gear import (
        axial_positions,
        compute_layout,
        gear_radii,
        yarn_paths,
    )
    from braidpy.horn_gear.word import annular_word, flat_word

    machines = _machines()
    name = str(spec.get("name", "tubular_8"))
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    machine = machines[name]()
    cycles = _count(spec, "cycles", 2, 1, 8)
    radii = gear_radii(machine)
    # A fifth of a gear radius is a plausible yarn.
    default = 0.2 * sum(radii.values()) / len(radii)
    diameter = _number(spec, "yarn_diameter", default, 0.01, 10.0)
    layout = compute_layout(machine)
    cores = axial_positions(machine, layout)
    notes = ["Words are read over one cycle of the machine."]
    if not cores:
        paths = yarn_paths(
            machine, n_cycles=cycles, yarn_diameter=diameter, fell_radius=0.0
        )
        paths = _tighten(paths, spec, diameter)
    elif len(cores) == 1:
        # Braided over a core as thick as a yarn: drawn in round it, and
        # kept outside it as the yarns are pulled tight.
        paths = yarn_paths(
            machine, n_cycles=cycles, yarn_diameter=diameter, fell_radius=diameter
        )
        paths = _tighten_round(paths, spec, diameter, core_radius=diameter / 2)
    else:
        # Several cores, side by side: each takes its own yarns, which no
        # single braiding point describes.  Laid as they come off.
        paths = yarn_paths(machine, n_cycles=cycles, yarn_diameter=diameter)
        notes.append(
            "It braids round several cores at once: its yarns are laid as "
            "they come off, not drawn in and tightened."
        )
    info: Dict[str, Any] = {}
    if cores:
        notes[0] = (
            "It braids round a core, which its word would need as a strand "
            "of its own: no word is given."
        )
    elif name.startswith("tubular"):
        annular = annular_word(machine)
        info["annular_word"] = " ".join(str(g) for g in annular.generators)
        info["crossings"] = len(annular.generators)
    else:
        info.update(_braid_info(flat_word(machine), len(paths.points)))
    result = _result(
        _MACHINE_TITLES[name] + f", {cycles} cycles",
        paths,
        diameter,
        info=info,
        notes=notes,
    )
    heights = [p[2] for strand in result["strands"] for p in strand["points"]]
    top, fell = float(max(heights)), float(min(heights))
    result["cores"] = [
        {
            "name": f"Core {core}",
            "diameter": diameter,
            "from": [round(x - paths.axis[0], 4), round(y - paths.axis[1], 4), fell],
            "to": [round(x - paths.axis[0], 4), round(y - paths.axis[1], 4), top],
        }
        for core, (x, y) in cores.items()
    ]
    return result


def _hues(n: int) -> List[str]:
    from braidpy.ashley_solid_sinnet import strand_colours

    return strand_colours(n)
