# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy's front door: a few questions about braids, answered in plain
data — for a person at a prompt, a script, or an AI assistant
(:mod:`braidpy.mcp_server` offers each as a tool).

Each function takes and gives only text, numbers, lists and dicts, so what
goes in and comes out can be read, printed or sent as JSON as it is.  None
does anything of its own: each asks the module that knows, and says which.

>>> from braidpy import tools
>>> tools.describe_braid("1 -2")["permutation"]
[2, 3, 1]
>>> tools.compare_braids("1 -2", "-2 1", n_strands=3)["same_braid"]
True

A braid is given as a braid word: signed generators, ``1`` for σ₁, ``-2``
for σ₂⁻¹, written as braidpy reads them (:func:`~braidpy.braidword.parse_word`):
``"1 -2"``, ``"1,-2"``, ``"s1 s2^-1"`` or ``"aB"``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode

from braidpy.braid import Braid

if TYPE_CHECKING:
    from braidpy.web import Spec

__all__ = [
    "STUDIO",
    "compare_braids",
    "describe_braid",
    "list_braids",
    "make_braid",
    "similar_braids",
    "studio_link",
    "ways_to_make",
]

#: Braid Studio, where a braid described here can be seen made.
STUDIO = "https://baptistelabat.github.io/braidpy/studio/"


def _braid(word: str, n_strands: int | None = None) -> Braid:
    """A braid word read, on as many strands as it needs if not said."""
    from braidpy.braidword import parse_word

    generators = parse_word(word)
    if not generators:
        raise ValueError(f"No crossing in {word!r}: give a braid word, say '1 -2'.")
    least = max(abs(g) for g in generators) + 1
    return Braid(tuple(generators), n_strands or least)


def studio_link(spec: dict[str, Any]) -> str:
    """Where Braid Studio makes a braid, from what describes it — a link to
    open, to see it in 3D, turn it, grow it.

    Args:
        spec: What :func:`braidpy.web.build` makes it from, for example
            ``{"source": "word", "word": "1 -2", "n_strands": 3}``.

    Returns:
        The link.
    """
    return STUDIO + "#" + urlencode({k: v for k, v in spec.items() if v is not None})


def list_braids(source: str | None = None) -> dict[str, Any]:
    """The braids braidpy knows by name, by what makes them: braid words,
    kumihimo disks, Ashley's sinnets, braiding machines, lace machines
    (:func:`braidpy.web.catalogue`).

    Args:
        source: Only this one, for example ``"sinnet"``; all if None.

    Returns:
        Per source, its title and its braids — each a ``name`` and a
        ``title`` — and the settings it takes, with their defaults.
    """
    from braidpy.web import catalogue

    listed = {
        name: {
            "title": about["title"],
            "defaults": about["defaults"],
            "braids": [
                {"name": e["name"], "title": e["title"]}
                for e in about.get("entries", [])
                if e["name"] != "custom"
            ]
            + [
                {"word": e["word"], "n_strands": e["n_strands"], "title": e["title"]}
                for e in about.get("examples", [])
            ],
        }
        for name, about in catalogue().items()
    }
    if source is None:
        return listed
    if source not in listed:
        raise ValueError(f"No source {source!r}: one of {sorted(listed)}.")
    return {source: listed[source]}


def describe_braid(word: str, n_strands: int | None = None) -> dict[str, Any]:
    """What is known of a braid from its word: strands, crossings, the
    permutation it makes, whether it is pure and after how many repeats,
    what it closes up into, its Garside normal form — as Braid Studio's
    card shows it (:mod:`braidpy.web`) — and a link to see it.

    Args:
        word: The braid word, for example ``"1 -2"``.
        n_strands: The strands; as many as the word needs if None.

    Returns:
        What is known, by name.
    """
    from braidpy.web._info import _braid_info

    braid = _braid(word, n_strands)
    word_given = [int(g) for g in braid.generators]
    info = dict(_braid_info(word_given, braid.n_strands))
    info["n_strands"] = braid.n_strands
    info["studio"] = studio_link(
        {
            "source": "word",
            "word": " ".join(map(str, word_given)),
            "n_strands": braid.n_strands,
        }
    )
    return info


def compare_braids(a: str, b: str, n_strands: int | None = None) -> dict[str, Any]:
    """Whether two braid words make the same braid, as braidpy compares
    braids — by their topology, however written
    (:func:`braidpy.ring_program.same_braid`) — and how unlike they are
    (:func:`braidpy.similarity.distance`: 0 the same, up to 5).

    Args:
        a: A braid word.
        b: Another.
        n_strands: The strands of both; as many as they need if None.

    Returns:
        ``same_braid`` and ``distance``.
    """
    from braidpy.similarity import distance, fingerprint, same_fingerprint

    n = n_strands or max(_braid(a).n_strands, _braid(b).n_strands)
    one, other = fingerprint(_braid(a, n)), fingerprint(_braid(b, n))
    return {
        "same_braid": same_fingerprint(one, other),
        "distance": round(float(distance(one, other)), 3),
    }


def similar_braids(
    word: str, n_strands: int | None = None, count: int = 5
) -> list[dict[str, Any]]:
    """The braids of braidpy's catalogues most like this one, nearest first,
    each with every way braidpy knows of making it
    (:func:`braidpy.topology_catalog.related`).

    Args:
        word: The braid word.
        n_strands: The strands; as many as the word needs if None.
        count: How many to give.

    Returns:
        Per braid: its ``title``, ``distance`` (0 is this very braid), and
        ``made_as``, each way of making it with a ``studio`` link.
    """
    from braidpy.topology_catalog import related

    found = []
    for topology, apart in related(_braid(word, n_strands), count=count):
        found.append(
            {
                "title": topology.title,
                "distance": round(float(apart), 3),
                "made_as": [
                    {
                        "source": method.source,
                        "title": method.title,
                        "studio": studio_link(dict(method.spec)),
                    }
                    for method in topology.methods
                ],
            }
        )
    return found


def ways_to_make(word: str, n_strands: int | None = None) -> dict[str, Any]:
    """How to make a braid by hand or on a machine (:mod:`braidpy.bridges`):
    a kumihimo disk's moves, a Jacquard lace machine's punchcard, and
    Ashley's stand — a sinnet of the book's kind if one makes it, or the
    braid itself one strand a space.

    Args:
        word: The braid word, one repeat of it.
        n_strands: The strands; as many as the word needs if None.

    Returns:
        ``disk``: its moves, from slot > to slot, and a ``studio`` link;
        ``lace``: the punchcard, as punched, and where the bobbins go;
        ``ashley``: its spaces, moves, whether it is ``a_sinnet`` of the
        book's kind, and a ``studio`` link.
    """
    from braidpy.bridges.ashley import ashley_moves, ashley_sinnet, sinnet_spec
    from braidpy.bridges.disk import disk_moves
    from braidpy.bridges.lace import lace_card

    braid = _braid(word, n_strands)
    made: dict[str, Any] = {}
    if 2 * braid.n_strands + 2 <= 32:
        disk = disk_moves(braid)
        made["disk"] = {"moves": disk.text(), "studio": studio_link(disk.spec())}
    card = lace_card(braid)
    made["lace"] = {"card": card.text(), "bobbins": card.notches()}
    search = ashley_sinnet(braid, time_limit=3.0)
    sinnet = search.sinnet or ashley_moves(braid)
    spec = sinnet_spec(sinnet)
    made["ashley"] = {
        "a_sinnet": search.sinnet is not None,
        "spaces": spec["counts"],
        "moves": spec["moves"],
        "studio": studio_link(spec),
    }
    return made


def make_braid(spec: dict[str, Any]) -> dict[str, Any]:
    """A braid made as Braid Studio makes it (:func:`braidpy.web.build`),
    told in words: what is known of it and what was noted on the way —
    not the thousands of points of its yarns, for which ``build`` itself,
    or the link, is the place.

    Args:
        spec: What it is made from, for example ``{"source": "sinnet",
            "name": "abok_3042"}``; see :func:`list_braids` for each
            source's settings.

    Returns:
        ``title``, ``info``, ``notes`` and a ``studio`` link.
    """
    from braidpy.web import build

    made = build(cast("Spec", spec), tighten=False)
    return {
        "title": made["title"],
        "info": made["info"],
        "notes": made.get("notes", []),
        "studio": studio_link(spec),
    }
