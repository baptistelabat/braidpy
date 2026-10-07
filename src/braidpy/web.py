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

import math
import re
from contextvars import ContextVar
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Hashable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np

__all__ = ["build", "catalogue", "parse_moves", "parse_word"]

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


def parse_moves(text: str) -> List[Tuple[int, int]]:
    """Moves from one place to another, as ``(from, to)`` pairs.

    Reads ``1>15, 17>31``, ``1->15; 17->31``, ``1 15, 17 31``, ``(1, 15)
    (17, 31)``, one move per line, and the like: what matters is the order
    of the numbers, taken two by two.

    Args:
        text: The moves.

    Returns:
        The moves, in order.

    Raises:
        ValueError: If there are no moves, or an odd number of places.
    """
    if re.search(r"[^\d\s,;:()\[\]>→\-]", text):
        raise ValueError("Write moves as from>to pairs, for example 1>15, 17>31.")
    numbers = [int(n) for n in re.findall(r"\d+", text)]
    if not numbers:
        raise ValueError("Give at least one move, for example 1>15.")
    if len(numbers) % 2:
        raise ValueError("Each move needs a place to go from and one to go to.")
    return list(zip(numbers[::2], numbers[1::2]))


def _numbers(text: Any, what: str) -> List[int]:
    numbers = [int(n) for n in re.findall(r"-?\d+", str(text))]
    if not numbers:
        raise ValueError(f"Give the {what}, as numbers.")
    return numbers


def _moves_text(moves: Sequence[Tuple[int, int]]) -> str:
    return ", ".join(f"{a}>{b}" for a, b in moves)


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
                {"word": "1 2 3", "n_strands": 4, "repeat": 12, "title": "Twist"},
                {
                    "word": "1 -2 3 -2",
                    "n_strands": 4,
                    "repeat": 4,
                    "title": "Four-strand flat",
                },
                {"word": "1 1 1", "n_strands": 2, "repeat": 8, "title": "Two-ply"},
                {
                    "layout": "ring",
                    "word": "4",
                    "n_strands": 3,
                    "repeat": 36,
                    "title": "Rope, as a ring word",
                },
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
                    "title": entry.name[0].upper()
                    + entry.name[1:]
                    + (
                        "" if "strand" in entry.name else f", {entry.n_strands} strands"
                    ),
                    "pattern": {
                        "n_slots": entry.n_slots,
                        "slots": " ".join(str(slot) for slot, _ in entry.initial_slots),
                        "moves": _moves_text(entry.moves),
                        "shift": entry.n_shift_after_cycle,
                    },
                }
                for key, entry in mobidais.items()
            ]
            + [{"name": "custom", "title": "Your own moves…"}],
        },
        "sinnet": {
            "title": "Ashley solid sinnet",
            "defaults": {"name": "abok_3042", "cycles": 3},
            "entries": [
                {
                    "name": name,
                    "title": f"ABOK #{name.split('_')[1]}, {sinnet.n_strands}-strand "
                    + (sinnet.shape or "sinnet"),
                    "shape": sinnet.shape,
                    "pattern": {
                        "counts": " ".join(
                            str(c) for c in sinnet.initial_counts_per_space
                        ),
                        "moves": _moves_text(sinnet.moves),
                    },
                }
                for name, sinnet in sinnets.items()
            ]
            + [{"name": "custom", "title": "Your own moves…"}],
        },
        "machine": {
            "title": "Horn gear braiding machine",
            "defaults": {"name": "tubular_8", "cores": "yarn", "cycles": 2},
            "entries": [
                {"name": name, "title": title}
                for name, title in _MACHINE_TITLES.items()
            ],
        },
    }


# -------------------------------------------------------------------- build


# Set while a braid is built for a page that tightens it itself: the yarns
# are then only laid, and what tightening them needs is handed over instead.
_PAGE_TIGHTENS: ContextVar[bool] = ContextVar("page_tightens", default=False)
_TIGHTENING: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "tightening", default=None
)


def build(spec: Mapping[str, Any], tighten: bool = True) -> Dict[str, Any]:
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
    later = _PAGE_TIGHTENS.set(not tighten)
    job = _TIGHTENING.set(None)
    try:
        return builders[source](spec)
    finally:
        _PAGE_TIGHTENS.reset(later)
        _TIGHTENING.reset(job)


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


def _tightened(
    paths,
    diameter: float,
    iterations: int,
    core_radius=None,
    rigid: Sequence[Hashable] = (),
):
    """The yarns pulled taut — or, for a page that does it itself, as laid,
    with what it needs to do so noted for :func:`_result`."""
    from braidpy.take_off import tighten_yarns

    if iterations == 0:
        return paths
    if _PAGE_TIGHTENS.get():
        formed = paths.formed()
        _TIGHTENING.set(
            {
                "n_yarns": int(formed.shape[0]),
                "n": int(formed.shape[1]),
                "spacing": float(paths._level_spacing()),
                "yarn_diameter": float(diameter),
                "iterations": int(iterations),
                # tighten_yarns' own defaults.
                "step": 20.0,
                "tolerance": 1e-3,
                "hold_top": True,
                "core_radius": None if core_radius is None else float(core_radius),
                "centre": [float(paths.axis[0]), float(paths.axis[1])],
                "xy": np.round(formed[:, :, :2].reshape(-1), 9).tolist(),
                "rigid": [k in rigid for k in paths.points],
            }
        )
        return paths
    tightened, _ = tighten_yarns(
        paths, diameter, iterations=iterations, core_radius=core_radius, rigid=rigid
    )
    return tightened


def _tighten(
    paths,
    spec: Mapping[str, Any],
    diameter: float,
    default: int = 150,
    rigid: Sequence[Hashable] = (),
):
    iterations = _count(spec, "iterations", default, 0, 2000)
    return _tightened(paths, diameter, iterations, rigid=rigid)


def _result(
    title: str,
    paths,
    diameter: float,
    colours: Optional[Sequence[str]] = None,
    names: Optional[Sequence[str]] = None,
    info: Optional[Dict[str, Any]] = None,
    notes: Sequence[str] = (),
    timeline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Everything the page draws, as plain data."""
    n = paths.formed_count
    keys: List[Hashable] = list(paths.points)
    stride = max(1, math.ceil(n / _MAX_POINTS))
    centre = np.array([paths.axis[0], paths.axis[1], 0.0])
    chosen = list(range(0, n, stride))
    if chosen[-1] != n - 1:
        chosen.append(n - 1)
    strands = []
    for i, key in enumerate(keys):
        points = np.asarray(paths.points[key], dtype=float)[chosen] - centre
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
    tightening = _TIGHTENING.get()
    if tightening is None:
        try:
            out_info["closest_approach"] = round(
                float(paths.closest_approach(include_fell=False)), _DECIMALS
            )
        except Exception:  # an estimate only; never worth failing the braid over
            pass
    result: Dict[str, Any] = {
        "title": title,
        "strands": strands,
        # When each point was laid, in the source's time: the same for
        # every yarn, since they are laid together.
        "times": np.round(np.asarray(paths.times)[chosen], _DECIMALS).tolist(),
        "yarn_diameter": diameter,
        "info": out_info,
        "notes": list(notes),
    }
    if timeline is not None:
        result["timeline"] = timeline
    if tightening is not None:
        # The axis taken off the strands' points is the tightening's centre.
        result["tighten"] = {**tightening, "chosen": chosen}
    return result


def _timeline(
    trajectories,
    keys: Sequence[Hashable],
    kind: str,
    clock: Optional[Dict[str, List[float]]] = None,
    ring=None,
) -> Dict[str, Any]:
    """What made the braid, seen from above, over time: for the page to
    animate in step with the braid.

    Args:
        trajectories: The carriers' paths.
        keys: The strands, in the order the braid gives them.
        kind: ``disk`` — strands drawn as spokes to the middle — or
            ``machine``, or ``line``.
        clock: The source's time at some instants, and the braid's then;
            the same times if None.
        ring: For a disk, the strands round the ring the braid was laid
            from: the braid then hangs from the disk turned so each strand
            at the fell is nearest its carrier — see
            :meth:`~braidpy.disk_animation.BraidGrowth.turn_at` — and how
            far it is turned is given at each instant, as ``turn``.
    """
    times = np.asarray(trajectories.times, dtype=float)
    stride = max(1, math.ceil(len(times) / 3000))
    chosen = list(range(0, len(times), stride))
    if chosen[-1] != len(times) - 1:
        chosen.append(len(times) - 1)
    cx, cy = trajectories.centre()
    shift = np.array([cx, cy])

    def plane(points) -> List[List[float]]:
        return np.round(np.asarray(points, dtype=float) - shift, 3).tolist()

    strands = [plane(trajectories.xy[k][chosen]) for k in keys]
    outlines = [
        plane(outline[:: max(1, len(outline) // 400)])
        for outline in trajectories.outlines
    ]
    reach = max(
        float(np.max(np.hypot(*(np.asarray(p) - shift).T)))
        for p in [*trajectories.xy.values(), *trajectories.outlines]
    )
    if clock is None:
        clock = {
            "source": [float(times[0]), float(times[-1])],
            "braid": [float(times[0]), float(times[-1])],
        }
    turn = None
    if ring is not None:
        rows = np.interp(times[chosen], clock["source"], clock["braid"])
        pull = np.zeros(len(chosen), dtype=complex)
        for k in keys:
            at = np.asarray(trajectories.xy[k][chosen], dtype=float) - shift
            on = np.asarray(ring.xy[k], dtype=float)
            x = np.interp(rows, ring.times, on[:, 0])
            y = np.interp(rows, ring.times, on[:, 1])
            carrier = at[:, 0] + 1j * at[:, 1]
            fell = x + 1j * y
            pull += (
                carrier
                / np.maximum(np.abs(carrier), 1e-12)
                * np.conj(fell / np.maximum(np.abs(fell), 1e-12))
            )
        turn = np.round(np.unwrap(np.angle(pull)), 4).tolist()
    return {
        "kind": kind,
        "times": np.round(times[chosen], _DECIMALS).tolist(),
        "strands": strands,
        "outlines": outlines,
        "slots": [
            [round(x - cx, 3), round(y - cy, 3), name]
            for x, y, name in trajectories.slots
        ],
        "reach": round(reach, 3),
        "clock": clock,
        **({"turn": turn} if turn is not None else {}),
    }


def _disk_program(
    start, steps, n_slots: int, clockwise: bool, keys: Sequence[Hashable]
) -> Dict[str, Any]:
    """What a disk does, for the page to make the braid itself, move by
    move: each strand's slot to start with, in the order of the strands
    given, and per step the strands that move, by index, and by how many
    slots."""
    index = {k: i for i, k in enumerate(keys)}
    return {
        "n_slots": int(n_slots),
        "clockwise": bool(clockwise),
        "start": [int(start[k]) for k in keys],
        "steps": [
            [[index[k], int(delta)] for k, delta in step.items() if delta]
            for step in steps
        ],
    }


def _disk_in_step(
    start,
    steps,
    n_slots: int,
    diameter: float,
    iterations: int,
    clockwise: bool,
):
    """A disk's braid, laid round a ring with its rows made in the order
    the disk makes their crossings — as the side view of
    :class:`~braidpy.disk_animation.BraidGrowth` does — so the page can show
    the disk and the braid in step.

    Returns:
        The braid, and its clock: the disk's time at each crossing, and the
        braid's then.
    """
    from braidpy.take_off import (
        crossing_rows,
        disk_crossing_steps,
        lay_yarns,
        ring_trajectories,
    )

    order, crossings, made_at = disk_crossing_steps(start, steps, n_slots)
    if not crossings:
        raise ValueError("These moves cross no strands: there is no braid.")
    rows = crossing_rows(order, crossings, in_turn=True)
    ring = ring_trajectories(order, crossings, diameter, clockwise=clockwise, rows=rows)
    paths = lay_yarns(ring, take_off=1.5 * diameter, yarn_diameter=diameter)
    paths = _tightened(paths, diameter, iterations)
    clock = {
        "source": [0.0, *map(float, made_at), float(len(steps))],
        "braid": [0.0, *(r + 0.5 for r in rows), float(rows[-1] + 1)],
    }
    return paths, clock, ring


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
        permutation = [int(p) for p in braid.perm()]
        info["permutation"] = permutation
        info["pure"] = bool(braid.is_pure())
        info["pure_after"] = _order(permutation)
        info["components"] = _cycles(permutation)
        # The Garside normal form costs more the more strands there are:
        # beyond this, minutes in a browser.
        if n_strands <= 12 and len(word) <= 300:
            factors = braid.get_canonical_factors()
            least = int(factors.n_half_twist)
            most = least + len(factors.Ai)
            info["garside"] = {
                "half_twists": least,
                "factors": len(factors.Ai),
                # As Braid.full_twists has it, without computing it twice.
                "full_twists": int(math.floor((least + most) / 4 + 0.5)),
            }
    return info


def _unit(info: Dict[str, Any], word: Sequence[int], n_strands: int, repeated: str):
    """Says in ``info`` how many of the braid's unit — its word repeated, or
    its moves' cycle, as ``repeated`` names it — make a pure braid."""
    from braidpy.braid import Braid

    word = [int(g) for g in word]
    info["pure_after"] = (
        _order([int(p) for p in Braid(word, n_strands).perm()]) if word else 1
    )
    info["repeated"] = repeated
    return info


def _disk_unit(
    info: Dict[str, Any],
    cycles: Callable[[int], Tuple[Any, Any, int]],
    clockwise: bool,
    repeated: str = "cycle",
):
    """:func:`_unit` for a disk braid, whose ``cycles(k)`` are the start,
    steps and slots of ``k`` cycles of its moves.  A braid that creeps round the disk
    from cycle to cycle, as kongo gumi does, is not its first cycle repeated:
    its cycles are counted until the braid is pure, up to
    :data:`_MOST_CYCLES`."""
    from braidpy.annulus_braid import solid_word
    from braidpy.braid import Braid
    from braidpy.take_off import disk_annular_word

    def permutation(k: int) -> List[int]:
        start, steps, n_slots = cycles(k)
        annular, n = disk_annular_word(start, steps, n_slots, clockwise=clockwise)
        word = solid_word(annular, n)
        return (
            [int(p) for p in Braid(word, n).perm()] if word else list(range(1, n + 1))
        )

    k: Optional[int] = _order(permutation(1))
    if k and k > 1 and _order(permutation(k)) != 1:
        k = next(
            (k for k in range(2, _MOST_CYCLES + 1) if _order(permutation(k)) == 1),
            None,
        )
    info["pure_after"] = k
    info["repeated"] = repeated
    return info


# Cycles counted, at most, to find when a creeping disk braid is pure.
_MOST_CYCLES = 64


def _order(permutation: Sequence[int]) -> int:
    """How many times a braid is repeated before it is pure, every strand
    back where it started: the least common multiple of its permutation's
    cycles' lengths."""
    seen = set()
    order = 1
    for start in range(len(permutation)):
        length = 0
        here = start
        while here not in seen:
            seen.add(here)
            here = permutation[here] - 1
            length += 1
        if length:
            order = order * length // math.gcd(order, length)
    return order


def _cycles(permutation: Sequence[int]) -> int:
    """How many separate pieces a braid's closure makes: its permutation's
    cycles."""
    seen = set()
    cycles = 0
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycles += 1
        here = start
        while here not in seen:
            seen.add(here)
            here = permutation[here] - 1
    return cycles


def _ring_moves(word: Sequence[int], n_strands: int) -> Tuple[List[int], bool]:
    """A flat braid word as moves on a ring of carriers, for the page to make
    it move by move as on a marudai: the row of strands rolled round the
    ring.

    A full run of crossings round the ring — ``σₙ₋₁…σ₁``, or its inverse
    ``σ₁⁻¹…σₙ₋₁⁻¹`` — is the bobbins all turning one place round
    (:func:`braidpy.annulus_braid.turn`), as a braider lays up a rope;
    carried out as crossings, one strand would go all the way round under
    the others.  Every other crossing is a swap of neighbours.  The ring is
    numbered whichever way round finds the more turns: the other way is a
    half turn of the whole braid about its axis, ``σᵢ`` read as ``σₙ₋ᵢ``.

    Returns:
        The moves — crossings ``±1`` to ``±(n - 1)``, turns ``±(n + 1)``, as
        :func:`braidpy.annulus_braid.solid_word` reads them — and whether
        the ring is numbered the other way round.
    """
    n = n_strands
    word = [int(g) for g in word]
    up = list(range(n - 1, 0, -1))
    down = [-g for g in reversed(up)]

    def rolled(letters: List[int]) -> List[int]:
        moves: List[int] = []
        k = 0
        while k < len(letters):
            if letters[k : k + n - 1] == up:
                moves.append(n + 1)
                k += n - 1
            elif letters[k : k + n - 1] == down:
                moves.append(-(n + 1))
                k += n - 1
            else:
                moves.append(letters[k])
                k += 1
        return moves

    straight = rolled(word)
    mirrored = rolled([(n - abs(g)) * (1 if g > 0 else -1) for g in word])
    if len(mirrored) < len(straight):
        return mirrored, True
    return straight, False


def _ring_program(
    moves: Sequence[int], n_strands: int, mirrored: bool
) -> Dict[str, Any]:
    """Ring moves (:func:`_ring_moves`) as a disk program for the page: the
    braid hanging free, as a disk braid does, and held only while the
    bobbins turn round it, twisting the yarns in.  Strand ``k`` starts in place ``k``
    round the ring, or ``n - 1 - k`` numbered the other way; each place is
    ``slots`` slots on from the last.

    A swap is three moves: the strand passing under goes most of the way
    first, the one passing over is then laid across it, and the first goes
    the rest of the way."""
    n = n_strands
    slots = 12
    at = [n - 1 - p if mirrored else p for p in range(n)]
    start = [0] * n
    for place, strand in enumerate(at):
        start[strand] = 1 + slots * place
    steps: List[List[List[int]]] = []
    for move in moves:
        index, sign = abs(move), (1 if move > 0 else -1)
        if index == n + 1:
            steps.append([[strand, sign * slots] for strand in range(n)])
            at = at[-1:] + at[:-1] if sign > 0 else at[1:] + at[:1]
            continue
        a, b = index - 1, index % n
        over, under = (at[b], at[a]) if sign > 0 else (at[a], at[b])
        way = slots if under == at[a] else -slots
        most = round(0.75 * way)
        steps.append([[under, most], [over, -way], [under, way - most]])
        at[a], at[b] = at[b], at[a]
    return {
        "n_slots": n * slots,
        "clockwise": False,
        "start": start,
        "steps": steps,
        "twists": True,
        # Nothing but turns is a rope: held all the while it is laid up.
        "held": all(abs(move) == n + 1 for move in moves),
    }


def _shortened(text: str, most: int = 32) -> str:
    """A long word cut short for a title."""
    text = " ".join(text.split())
    return text if len(text) <= most else text[:most].rsplit(" ", 1)[0] + " …"


def _from_word(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.annulus_braid import solid_word
    from braidpy.braid import Braid
    from braidpy.take_off import braid_word_trajectories, lay_yarns

    layout = str(spec.get("layout", "row"))
    if layout not in ("row", "ring"):
        raise ValueError("Strands are either in a row or round a ring.")
    ring = layout == "ring"
    word = parse_word(str(spec.get("word", "")))
    if not word:
        raise ValueError("Give a braid word, for example 1 -2.")
    repeat = _count(spec, "repeat", 1, 1, 50)
    top = max(abs(g) for g in word)
    if ring:
        # Round a ring, the greatest move is taken for the seam's crossing.
        n_strands = _count(spec, "n_strands", max(top, 2), 2, 32)
        if top > n_strands + 1:
            raise ValueError(
                f"On a ring of {n_strands} strands, moves go up to "
                f"{n_strands + 1}, a turn."
            )
        moves = word * repeat
        word = solid_word(moves, n_strands)
        if not word:
            raise ValueError("That ring word crosses nothing once laid flat.")
    else:
        needed = top + 1
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
    info = _braid_info(word, n_strands)
    once = (
        solid_word(moves[: len(moves) // repeat], n_strands)
        if ring
        else word[: len(word) // repeat]
    )
    _unit(info, once, n_strands, "repeat")
    if ring:
        info["annular_word"] = " ".join(str(g) for g in moves)
    result = _result(
        ("Ring word " if ring else "Braid word ")
        + _shortened(str(spec.get("word", "")))
        + (f", {repeat} times" if repeat > 1 else ""),
        paths,
        diameter,
        info=info,
        timeline=_timeline(trajectories, list(paths.points), "line"),
    )
    # Made move by move round a ring: a ring word as it is written, a braid
    # word rolled onto the ring.
    if ring:
        result["disk"] = _ring_program(moves, n_strands, False)
    else:
        rolled, mirrored = _ring_moves(word, n_strands)
        result["disk"] = _ring_program(rolled, n_strands, mirrored)
    result["info"]["made"] = repeat
    return result


def _disk_info(start, steps, n_slots: int, clockwise: bool) -> Dict[str, Any]:
    """A disk braid's word, read round the ring and with the middle solid."""
    from braidpy.annulus_braid import solid_word
    from braidpy.take_off import disk_annular_word

    annular, n = disk_annular_word(start, steps, n_slots, clockwise=clockwise)
    info = _braid_info(solid_word(annular, n), n)
    info["annular_word"] = " ".join(str(g) for g in annular)
    return info


def _kumihimo_cycles(pattern: str, n_strands: int):
    from braidpy.take_off import kumihimo_steps

    n_slots, start, steps = kumihimo_steps(pattern, n_strands)
    return start, steps, n_slots


def _from_kumihimo(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.take_off import kumihimo_steps, kumihimo_trajectories

    pattern = re.sub(r"\s+", "", str(spec.get("pattern", "SR"))).upper()
    if not pattern or set(pattern) - {"S", "R"}:
        raise ValueError("A kumihimo pattern is made of S (swap) and R (rotate).")
    n_strands = _count(spec, "n_strands", 8, 4, 32)
    if n_strands % 4:
        raise ValueError("Kumihimo needs a multiple of 4 strands.")
    repeat = _count(spec, "repeat", 8, 1, 50)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    n_slots, start, steps = kumihimo_steps(pattern * repeat, n_strands)
    paths, clock, ring = _disk_in_step(
        start,
        steps,
        n_slots,
        diameter,
        _count(spec, "iterations", 200, 0, 2000),
        clockwise=False,
    )
    disk = kumihimo_trajectories(pattern * repeat, n_strands)
    result = _result(
        f"Kumihimo {pattern} × {repeat}, {n_strands} strands",
        paths,
        diameter,
        colours=_hues(n_strands),
        info=_disk_unit(
            _disk_info(start, steps, n_slots, clockwise=False),
            lambda k: _kumihimo_cycles(pattern * k, n_strands),
            False,
            "repeat",
        ),
        timeline=_timeline(disk, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(start, steps, n_slots, False, list(paths.points))
    result["info"]["made"] = repeat
    return result


def _from_mobidai(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.take_off import mobidai_steps, mobidai_trajectories

    from braidpy.mobidai_catalog import CataloguedBraid

    mobidais = _mobidais()
    name = str(spec.get("name", "KONGO_8"))
    if name == "custom":
        n_slots = _count(spec, "n_slots", 32, 3, 128)
        slots = _numbers(spec.get("slots", ""), "slots the strands start in")
        if len(set(slots)) < len(slots):
            raise ValueError("Two strands start in the same slot.")
        if not all(1 <= slot <= n_slots for slot in slots):
            raise ValueError(f"Slots are numbered from 1 to {n_slots}.")
        moves = parse_moves(str(spec.get("moves", "")))
        if not all(1 <= p <= n_slots for move in moves for p in move):
            raise ValueError(f"Moves are between slots 1 to {n_slots}.")
        entry = CataloguedBraid(
            name="your own disk braid",
            n_slots=n_slots,
            initial_slots=tuple(zip(slots, _hues(len(slots)))),
            moves=tuple(moves),
            n_shift_after_cycle=_count(spec, "shift", 0, -128, 128),
            source="",
        )
    elif name in mobidais:
        entry = mobidais[name]
    else:
        raise ValueError(f"No mobidai braid {name!r}: one of {sorted(mobidais)}.")
    config = entry.to_config()
    cycles = _count(spec, "cycles", 6, 1, 40)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    start, steps = mobidai_steps(config, cycles)
    clockwise = getattr(config, "is_clockwise", True)
    paths, clock, ring = _disk_in_step(
        start,
        steps,
        config.n_slots,
        diameter,
        _count(spec, "iterations", 200, 0, 2000),
        clockwise=clockwise,
    )
    # Coloured by strand, in the order the braid gives them.
    colour_of = {k: colour for k, (_, colour) in zip(start, entry.initial_slots)}
    disk = mobidai_trajectories(config, n_cycles=cycles, slot_offset=0.5)
    result = _result(
        f"{entry.name[0].upper()}{entry.name[1:]}, {cycles} cycles",
        paths,
        diameter,
        colours=[colour_of[k] for k in paths.points],
        info=_disk_unit(
            _disk_info(start, steps, config.n_slots, clockwise),
            lambda k: (*mobidai_steps(config, k), config.n_slots),
            clockwise,
        ),
        timeline=_timeline(disk, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(
        start, steps, config.n_slots, clockwise, list(paths.points)
    )
    result["info"]["made"] = cycles
    return result


def _from_sinnet(spec: Mapping[str, Any]) -> Dict[str, Any]:
    from braidpy.ashley_solid_sinnet import strand_colours
    from braidpy.take_off import disk_trajectories

    from braidpy.ashley_solid_sinnet import AshleySolidSinnet

    sinnets = _sinnets()
    name = str(spec.get("name", "abok_3042"))
    if name == "custom":
        counts = _numbers(spec.get("counts", ""), "strands in each space")
        if len(counts) < 2 or min(counts) < 0 or sum(counts) < 2:
            raise ValueError("Give two spaces or more, holding two strands or more.")
        if sum(counts) > 64:
            raise ValueError("That is over 64 strands.")
        moves = parse_moves(str(spec.get("moves", "")))
        if not all(1 <= p <= len(counts) for move in moves for p in move):
            raise ValueError(f"Moves are between spaces 1 to {len(counts)}.")
        sinnet = AshleySolidSinnet(counts, moves)
    elif name in sinnets:
        sinnet = sinnets[name]
    else:
        raise ValueError(f"No sinnet {name!r}: one of {sorted(sinnets)}.")
    cycles = _count(spec, "cycles", 3, 1, 12)
    diameter = _number(spec, "yarn_diameter", 0.12, 0.02, 0.5)
    disk = sinnet.disk(cycles)
    paths, clock, ring = _disk_in_step(
        disk.start,
        disk.steps,
        disk.n_slots,
        diameter,
        _count(spec, "iterations", 200, 0, 2000),
        clockwise=False,
    )
    seen = disk_trajectories(
        disk.start,
        disk.steps,
        disk.n_slots,
        clockwise=False,
        slot_offset=disk.slot_offset,
        slot_names={
            disk.middle_slot(space): str(space) for space in range(1, disk.n_spaces + 1)
        },
    )
    seen = _with_sectors(seen, disk)
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
    called = "Your own" if name == "custom" else f"ABOK #{name.split('_')[1]},"
    info = _disk_info(disk.start, disk.steps, disk.n_slots, clockwise=False)

    def worked(k: int):
        made = sinnet.disk(k)
        return made.start, made.steps, made.n_slots

    # Cycles that do not come back to the counts they started from do not
    # repeat: there is no saying when they are pure.
    if not notes:
        _disk_unit(info, worked, False)
    if sinnet.shape:
        info["expected_shape"] = sinnet.shape
    result = _result(
        f"{called} {sinnet.n_strands}-strand {sinnet.shape or 'sinnet'}, "
        f"{cycles} cycles",
        paths,
        diameter,
        colours=[strand_colours(sinnet.n_strands)[int(k) - 1] for k in paths.points],
        info=info,
        notes=notes,
        timeline=_timeline(seen, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(
        disk.start, disk.steps, disk.n_slots, False, list(paths.points)
    )
    result["info"]["made"] = cycles
    return result


def _with_sectors(seen, disk):
    """A sinnet's disk as the book draws it: its spaces as sectors, a line
    from the middle to the rim half a slot before each space's first."""
    import dataclasses

    from braidpy.take_off import _disk_point

    lines = tuple(
        _disk_point(
            np.full(2, (space - 1) * disk.slots_per_space + 0.5),
            np.array([0.0, 1.0]),
            disk.n_slots,
            False,
            disk.slot_offset,
        )
        for space in range(1, disk.n_spaces + 1)
    )
    return dataclasses.replace(seen, outlines=seen.outlines + lines)


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
    stiff = str(spec.get("cores", "yarn"))
    if stiff not in ("yarn", "rigid"):
        raise ValueError("Cores are either yarn or rigid.")
    # The cores run up the braid, each in its own place, where the machine
    # lays it; the yarns are drawn in round them.  A rigid core stays
    # straight there; a core of yarn is held there at both ends, and gives
    # way between to the yarns pressing on it — never so far as to pass
    # another core.
    # Loaded by hand, or as the machine loads itself.  Carriers that meet
    # stop the machine: the braid is what it made until then.
    loading = _loading(spec.get("carriers"), machine)
    carriers_at = None if loading is None else dict(enumerate(loading))
    stopped = None
    n_steps = None
    if carriers_at is not None:
        from braidpy.horn_gear.simulation import (
            CollisionError,
            simulate,
            state_period,
        )

        period = state_period(machine, carriers_at) or machine.contact_period()
        n_steps = cycles * period
        try:
            simulate(machine, n_steps, carriers_at)
        except CollisionError as error:
            stopped = error
            n_steps = error.step - 1
            if n_steps < 1:
                raise ValueError(
                    "Those carriers meet as soon as the machine turns: "
                    + _met(error)
                    + "."
                ) from None
    paths = yarn_paths(
        machine,
        n_steps=n_steps,
        carrier_positions=carriers_at,
        n_cycles=cycles,
        yarn_diameter=diameter,
        fell_radius=0.0,
        axials=True,
    )
    paths = _place_cores(paths, cores)
    paths = _tighten(
        paths, spec, diameter, rigid=list(cores) if stiff == "rigid" else []
    )
    info: Dict[str, Any] = {}
    notes = ["Words are read over one cycle of the machine."]
    if stopped is not None:
        # The carriers that met, where they started: as the page draws
        # the machine, before it turns.
        assert loading is not None
        info["collision"] = {
            "step": int(stopped.step),
            "at": [
                [loading[k][0], int(loading[k][1])]
                for ids in stopped.collisions.values()
                for k in ids
            ],
        }
        notes = [
            f"Carriers met at step {stopped.step}, on {_met(stopped)}: the "
            f"braiding stopped there, after {n_steps} steps. The carriers that "
            "met are ringed where they started. No word is read."
        ]
    elif cores:
        notes = [
            "It braids round a core, drawn here in grey as the yarn it is; its "
            "word would need the core as a strand of its own: no word is given."
        ]
    elif name.startswith("tubular"):
        annular = annular_word(machine, carriers=carriers_at)
        info["annular_word"] = " ".join(str(g) for g in annular.generators)
        info["crossings"] = len(annular.generators)
    else:
        # Read over one cycle of the machine.
        info.update(
            _braid_info(flat_word(machine, carriers=carriers_at), len(paths.points))
        )
        info["repeated"] = "cycle"
        info["made"] = cycles
        # The cycles made, not the one read.
        info["pure"] = cycles % info.get("pure_after", 1) == 0
    keys = list(paths.points)
    carriers = [k for k in keys if k not in cores]
    colour = {k: _PALETTE[i % len(_PALETTE)] for i, k in enumerate(carriers)}
    colour.update({k: "#8a857c" for k in cores})
    return _result(
        _MACHINE_TITLES[name] + f", {cycles} cycles",
        paths,
        diameter,
        colours=[colour[k] for k in keys],
        names=[f"Core {k}" if k in cores else f"Yarn {k}" for k in keys],
        info=info,
        notes=notes,
        timeline=_timeline(paths.trajectories, keys, "machine"),
    )


def _loading(text: Any, machine: Any) -> Optional[List[Tuple[str, int]]]:
    """Carriers given as ``gear:slot``, each once; None if not given."""
    if text is None or not str(text).strip():
        return None
    if str(text).strip().lower() == "none":
        raise ValueError("Give at least one carrier.")
    loading: List[Tuple[str, int]] = []
    for token in re.split(r"[\s,;]+", str(text).strip()):
        match = re.fullmatch(r"([^:\s]+):(\d+)", token)
        if not match:
            raise ValueError(f"Cannot read {token!r}: give each carrier as gear:slot.")
        gear, slot = match.group(1), int(match.group(2))
        if gear not in machine.gears:
            raise ValueError(f"No gear {gear!r}: one of {sorted(machine.gears)}.")
        n = machine.gears[gear].n_slots
        if slot >= n:
            raise ValueError(f"Gear {gear} has slots 0 to {n - 1}.")
        if (gear, slot) in loading:
            raise ValueError(f"Two carriers on the same slot, {gear}:{slot}.")
        loading.append((gear, slot))
    if not loading:
        raise ValueError("Give at least one carrier.")
    return loading


def _met(error: Any) -> str:
    """Where carriers met, as gear:slot."""
    return " and ".join(f"{g}:{slot}" for g, slot in error.collisions)


def machine_geometry(name: str) -> Dict[str, Any]:
    """A machine as the page draws it from above, to load it by hand: its
    gears — where, how big, the circle their carriers ride, their slots, the
    way they turn and where their first slot is — the contacts between them,
    and the machine's own loading.  A slot's angle at step ``t`` is
    ``offset + 2π (slot + direction · t) / slots``."""
    from braidpy.horn_gear.layout import (
        carrier_radius,
        compute_layout,
        contact_point,
        gear_radii,
        slot_offsets,
    )

    machines = _machines()
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    machine = machines[name]()
    layout = compute_layout(machine)
    radii = gear_radii(machine)
    offsets = slot_offsets(machine, layout)
    own = machine.default_carriers()
    return {
        "name": name,
        "gears": [
            {
                "name": gear_name,
                "x": float(layout[gear_name][0]),
                "y": float(layout[gear_name][1]),
                "radius": float(radii[gear_name]),
                "ride": float(carrier_radius(machine, layout, gear_name)),
                "slots": int(gear.n_slots),
                "direction": int(gear.direction),
                "offset": float(offsets[gear_name]),
            }
            for gear_name, gear in machine.gears.items()
        ],
        "contacts": [
            {
                "a": conn.gear_a,
                "b": conn.gear_b,
                "x": float(point[0]),
                "y": float(point[1]),
            }
            for conn in machine.connections
            for point in [contact_point(machine, layout, conn.gear_a, conn.gear_b)]
        ],
        "loading": [[own[k][0], int(own[k][1])] for k in sorted(own)],
    }


def _place_cores(paths, cores: Collection[Hashable]):
    """The cores, each standing straight in the braid where the machine
    lays it, all the way down to the fell: drawn in to the braiding point
    with the yarns, the cores would meet there, and could pass each other."""
    from dataclasses import replace

    if not cores:
        return paths
    points = dict(paths.points)
    n = paths.formed_count
    for k in cores:
        line = points[k].copy()
        line[:n, :2] = line[0, :2]
        points[k] = line
    return replace(paths, points=points)


def _hues(n: int) -> List[str]:
    from braidpy.ashley_solid_sinnet import strand_colours

    return strand_colours(n)
