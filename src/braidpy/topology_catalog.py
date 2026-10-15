# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids by their topology, and the ways each is made.

Every other catalogue lists braids by how they are made: as a braid word
(:mod:`braidpy.braid_catalog`), on a kumihimo disk
(:mod:`braidpy.mobidai_catalog`), as one of Ashley's solid sinnets
(:mod:`braidpy.solid_sinnets_catalog`), on a braiding machine
(:mod:`braidpy.machine_catalog`).  Different ways can make the same braid:
the plait is a braid word, and what a three-carrier flat braiding machine
makes.  This catalogue lists braids by what they are — their
:func:`~braidpy.similarity.fingerprint` — each pointing to every way of
making it, and each way pointing back (:func:`topology_of`).  For a braid
of your own, :func:`related` gives the topologies nearest it.

A way of making a braid is a :class:`Method`: a source and an entry of its
catalogue, with the description Braid Studio makes it from
(:func:`braidpy.web.build`).  Its braid word is the one braidpy reads off
it, over a whole period: for a disk braid that creeps round the disk from
cycle to cycle, as kongo gumi does, as many cycles as bring every strand
home.  A machine braiding round cores has no braid word of its strands
alone, and is left out.

Building the catalogue makes every braid of every catalogue — some ten
seconds — so it is built once, when first asked for (:func:`catalogue`).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from braidpy.braid import Braid
from braidpy.catalogue import Entry
from braidpy.similarity import Fingerprint, distance, fingerprint, same_fingerprint

__all__ = ["Method", "Topology", "catalogue", "methods", "related", "topology_of"]


@dataclass(frozen=True)
class Method:
    """One way of making a braid.

    Args:
        source: Which catalogue: ``word``, ``kumihimo``, ``mobidai``,
            ``sinnet`` or ``machine``, as :func:`braidpy.web.build` has them.
        name: The braid's name in that catalogue.
        title: What it is called, to show.
        spec: What :func:`braidpy.web.build` makes it from.
    """

    source: str
    name: str
    title: str
    spec: Tuple[Tuple[str, Any], ...]

    @property
    def key(self) -> str:
        """``source:name``, unique across the catalogues."""
        return f"{self.source}:{self.name}"

    def description(self) -> Dict[str, Any]:
        """The description :func:`braidpy.web.build` makes it from."""
        return dict(self.spec)


@dataclass(frozen=True)
class Topology:
    """A braid, as what it is: its fingerprint, and every way of making it.

    Args:
        name: The name it is listed by: its first method's.
        title: What it is called: its first method's title.
        fingerprint: Its fingerprint.
        methods: The ways of making it, in the order the catalogues list
            them.
    """

    name: str
    title: str
    fingerprint: Fingerprint
    methods: Tuple[Method, ...]


def _spec(**items: Any) -> Tuple[Tuple[str, Any], ...]:
    return tuple(items.items())


def methods() -> List[Method]:
    """Every way of making a braid the catalogues list, in their order:
    braid words, kumihimo, kumihimo disks, sinnets, machines.

    Returns:
        The methods.
    """
    from braidpy.braid_catalog import CATALOGUE as WORDS
    from braidpy.braid_catalog import word_examples
    from braidpy.web import catalogue as studio

    listed = studio()
    found: List[Method] = []
    names = list(WORDS) + [
        example["title"].lower().replace(",", "").replace(" ", "_")
        for example in word_examples()[len(WORDS) :]
    ]
    for name, example in zip(names, word_examples()):
        rest = {k: v for k, v in example.items() if k != "title"}
        found.append(
            Method("word", name, example["title"], _spec(source="word", **rest))
        )
    pattern = listed["kumihimo"]["defaults"]
    found.append(
        Method(
            "kumihimo",
            str(pattern["pattern"]),
            f"Kumihimo {pattern['pattern']}, {pattern['n_strands']} strands",
            _spec(
                source="kumihimo",
                pattern=pattern["pattern"],
                n_strands=pattern["n_strands"],
                repeat=1,
            ),
        )
    )
    for source in ("mobidai", "sinnet", "machine"):
        for entry in listed[source]["entries"]:
            if entry["name"] == "custom":
                continue
            found.append(
                Method(
                    source,
                    entry["name"],
                    entry["title"],
                    _spec(source=source, name=entry["name"], cycles=1),
                )
            )
    return found


def _braid(method: Method) -> Optional[Braid]:
    """The braid a method makes, over a whole period; None if it has no
    braid word."""
    from braidpy.annulus_braid import solid_word
    from braidpy.pure_braid import closing_repeats
    from braidpy.web import build

    spec: Any = {**method.description(), "iterations": 0}
    info = build(spec, tighten=False)["info"]
    if "word" in info:
        braid = Braid(tuple(int(g) for g in info["word"].split()), info["n_strands"])
        # A disk braid that creeps round the disk is not its first cycle
        # repeated: its period is as many cycles as bring every strand
        # home.
        period = info.get("pure_after")
        if (
            method.source == "mobidai"
            and period
            and period != closing_repeats(braid, limit=None)
        ):
            info = build({**spec, "cycles": period}, tighten=False)["info"]
            braid = Braid(tuple(int(g) for g in info["word"].split()), braid.n_strands)
        return braid
    if "annular_word" in info:
        # A tubular machine's braid round its ring, the middle filled in.
        moves = [int(g) for g in info["annular_word"].split()]
        n = max(abs(g) for g in moves)
        return Braid(tuple(solid_word(moves, n)), n)
    return None


@lru_cache(maxsize=1)
def _topologies() -> Tuple[Topology, ...]:
    grouped: List[Tuple[Fingerprint, List[Method]]] = []
    for method in methods():
        braid = _braid(method)
        if braid is None:
            continue
        mark = fingerprint(braid)
        for known, members in grouped:
            if same_fingerprint(known, mark):
                members.append(method)
                break
        else:
            grouped.append((mark, [method]))
    return tuple(
        Topology(members[0].name, members[0].title, mark, tuple(members))
        for mark, members in grouped
    )


def catalogue() -> Dict[str, Entry[Topology]]:
    """The catalogue, as every catalogue lists its braids
    (:mod:`braidpy.catalogue`): an entry per topology, by its first
    method's name.  Built the first time it is asked for.

    Returns:
        The entries.
    """

    def entry(topology: Topology) -> Entry[Topology]:
        return Entry(
            topology.title,
            lambda: topology,
            ", ".join(f"{m.source}: {m.title}" for m in topology.methods),
        )

    return {topology.name: entry(topology) for topology in _topologies()}


def topology_of(source: str, name: str) -> Optional[Topology]:
    """The topology a catalogue's braid has: the way back from a method.

    Args:
        source: Its catalogue, as in :class:`Method`.
        name: Its name there.

    Returns:
        Its topology; None if it has no braid word.
    """
    key = f"{source}:{name}"
    for topology in _topologies():
        if any(m.key == key for m in topology.methods):
            return topology
    return None


def related(braid: Braid, count: int = 5) -> List[Tuple[Topology, float]]:
    """The topologies nearest a braid — one of your own, say — nearest
    first; distance 0 for its own, if the catalogue has it.

    Args:
        braid: The braid.
        count: How many to give.

    Returns:
        Up to ``count`` topologies, each with its
        :func:`~braidpy.similarity.distance`.
    """
    mine = fingerprint(braid)
    scored = [(t, distance(mine, t.fingerprint)) for t in _topologies()]
    scored.sort(
        key=lambda pair: (
            not same_fingerprint(mine, pair[0].fingerprint),
            pair[1],
            pair[0].name,
        )
    )
    return scored[:count]
