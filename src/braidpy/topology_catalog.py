# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids by their topology, and the ways each is made.

Every other catalogue lists braids by how they are made: as a braid word
(:mod:`braidpy.braid_catalog`), on a kumihimo disk
(:mod:`braidpy.mobidai_catalog`), as one of Ashley's solid sinnets
(:mod:`braidpy.solid_sinnets_catalog`), on a braiding machine
(:mod:`braidpy.machine_catalog`).  Different ways can make the same braid:
the plait is a braid word, Ashley's #2965 on his stand, and what a
three-carrier flat braiding machine makes.  This catalogue lists braids by what they are — their
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
Braid Studio has it built with the site: :func:`export` writes it as JSON,
:func:`load` reads it back, and :func:`for_page` says, for the braid on the
page, every other way of making it and the braids nearest it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from braidpy.braid import Braid
from braidpy.catalogue import Entry
from braidpy.similarity import Fingerprint, distance, fingerprint, same_fingerprint

__all__ = [
    "Method",
    "Topology",
    "braid_of",
    "catalogue",
    "export",
    "for_page",
    "load",
    "methods",
    "related",
    "topology_of",
]

# What says how much of a braid is made, not which braid it is.
_HOW_MUCH = ("cycles", "repeat")


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

    def describes(self, spec: Mapping[str, Any]) -> bool:
        """Whether a description is of this method's braid, however much of
        it is made: as a page's address has it, every value a string."""
        return all(
            key in _HOW_MUCH or str(spec.get(key)) == str(value)
            for key, value in self.spec
        )


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


def braid_of(info: Mapping[str, Any]) -> Optional[Braid]:
    """The braid :func:`braidpy.web.build` made, from what it says of it:
    its braid word, or, for a tubular machine, its word round the ring with
    the middle filled in.

    Args:
        info: The result's ``info``.

    Returns:
        The braid; None if it has no braid word.
    """
    from braidpy.annulus_braid import solid_word

    if info.get("word"):
        word = tuple(int(g) for g in info["word"].split())
        return Braid(word, info["n_strands"])
    if info.get("annular_word"):
        moves = [int(g) for g in info["annular_word"].split()]
        n = max(abs(g) for g in moves)
        return Braid(tuple(solid_word(moves, n)), n)
    return None


def _braid(method: Method) -> Optional[Braid]:
    """The braid a method makes, over a whole period; None if it has no
    braid word."""
    from braidpy.pure_braid import closing_repeats
    from braidpy.web import build

    spec: Any = {**method.description(), "iterations": 0}
    info = build(spec, tighten=False)["info"]
    braid = braid_of(info)
    # A disk braid that creeps round the disk is not its first cycle
    # repeated: its period is as many cycles as bring every strand home.
    period = info.get("pure_after")
    if (
        braid is not None
        and method.source == "mobidai"
        and period
        and period != closing_repeats(braid, limit=None)
    ):
        braid = braid_of(build({**spec, "cycles": period}, tighten=False)["info"])
    return braid


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


def topology_of(
    source: str, name: str, topologies: Optional[Sequence[Topology]] = None
) -> Optional[Topology]:
    """The topology a catalogue's braid has: the way back from a method.

    Args:
        source: Its catalogue, as in :class:`Method`.
        name: Its name there.
        topologies: Where to look; by default this catalogue.

    Returns:
        Its topology; None if it has no braid word.
    """
    key = f"{source}:{name}"
    for topology in _topologies() if topologies is None else topologies:
        if any(m.key == key for m in topology.methods):
            return topology
    return None


def related(
    braid: Braid,
    count: int = 5,
    topologies: Optional[Sequence[Topology]] = None,
) -> List[Tuple[Topology, float]]:
    """The topologies nearest a braid — one of your own, say — nearest
    first; distance 0 for its own, if the catalogue has it.

    Args:
        braid: The braid.
        count: How many to give.
        topologies: Where to look; by default this catalogue.

    Returns:
        Up to ``count`` topologies, each with its
        :func:`~braidpy.similarity.distance`.
    """
    return _nearest(fingerprint(braid), count, topologies)


def _nearest(
    mine: Fingerprint, count: int, topologies: Optional[Sequence[Topology]]
) -> List[Tuple[Topology, float]]:
    scored = [
        (t, distance(mine, t.fingerprint))
        for t in (_topologies() if topologies is None else topologies)
    ]
    scored.sort(
        key=lambda pair: (
            not same_fingerprint(mine, pair[0].fingerprint),
            pair[1],
            pair[0].name,
        )
    )
    return scored[:count]


def export() -> List[Dict[str, Any]]:
    """The catalogue as JSON-ready data, for :func:`load` to read back
    without making every braid again.

    Returns:
        Per topology, its name, title, fingerprint and methods.
    """
    return [
        {
            "name": t.name,
            "title": t.title,
            "fingerprint": asdict(t.fingerprint),
            "methods": [
                {
                    "source": m.source,
                    "name": m.name,
                    "title": m.title,
                    "spec": m.description(),
                }
                for m in t.methods
            ],
        }
        for t in _topologies()
    ]


def load(data: Sequence[Mapping[str, Any]]) -> Tuple[Topology, ...]:
    """The catalogue, from what :func:`export` wrote.

    Args:
        data: The exported data.

    Returns:
        The topologies.
    """
    found = []
    for t in data:
        mark = dict(t["fingerprint"])
        found.append(
            Topology(
                t["name"],
                t["title"],
                Fingerprint(
                    n_strands=int(mark["n_strands"]),
                    loops=tuple(mark["loops"]),
                    writhe=int(mark["writhe"]),
                    linking=tuple(mark["linking"]),
                    alexander=tuple(mark["alexander"]),
                ),
                tuple(
                    Method(m["source"], m["name"], m["title"], tuple(m["spec"].items()))
                    for m in t["methods"]
                ),
            )
        )
    return tuple(found)


def for_page(
    spec: Mapping[str, Any],
    info: Mapping[str, Any],
    topologies: Sequence[Topology],
    count: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """What Braid Studio shows of the braid it made, beside it: the other
    ways of making it, and the braids nearest it.

    A braid of the catalogues is known by its description, and has the
    fingerprint of its whole period; any other — your own — by the
    fingerprint of the braid made.

    Args:
        spec: The description the braid was made from.
        info: What :func:`braidpy.web.build` said of it.
        topologies: The catalogue (:func:`load`).
        count: How many nearest braids to give.

    Returns:
        ``same``: the methods making a braid with the same fingerprint,
        but the one shown; ``near``: the nearest other topologies, each
        with its ``distance``.  Each has a ``title`` and ``source`` to show
        and the ``spec`` to make it from, as much of it as the page makes
        by default.  Both are empty for a braid with
        no braid word.
    """
    mine: Optional[Fingerprint] = None
    shown: Optional[Method] = None
    for topology in topologies:
        for method in topology.methods:
            if method.source == spec.get("source") and method.describes(spec):
                mine, shown = topology.fingerprint, method
                break
        if shown:
            break
    if mine is None:
        braid = braid_of(info)
        if braid is None or not braid.generators:
            return {"same": [], "near": []}
        mine = fingerprint(braid)

    def card(method: Method) -> Dict[str, Any]:
        # Made as much as the page makes of it, not one cycle.
        spec = {k: v for k, v in method.spec if k not in _HOW_MUCH}
        return {"source": method.source, "title": method.title, "spec": spec}

    same: List[Dict[str, Any]] = []
    near: List[Dict[str, Any]] = []
    for topology, apart in _nearest(mine, len(topologies), topologies):
        if same_fingerprint(mine, topology.fingerprint):
            same.extend(card(m) for m in topology.methods if m != shown)
        elif len(near) < count:
            near.append({**card(topology.methods[0]), "distance": round(apart, 2)})
    return {"same": same, "near": near}
