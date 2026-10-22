# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Bridges from a braid to the ways of making it: each through a
:class:`~braidpy.ring_program.RingProgram`, and each checked by reading the
braid back off what it made.  See ``docs/source/bridges.md``.

- :mod:`braidpy.bridges.lace`: the Jacquard lace machine's punchcard;
- :mod:`braidpy.bridges.disk`: moves on a kumihimo disk;
- :mod:`braidpy.bridges.ashley`: a sinnet on Ashley's stand, by searching.
"""

from typing import TYPE_CHECKING, Any, Dict, Mapping

if TYPE_CHECKING:
    from braidpy.braid import Braid

# Longest repeating unit the page is given bridges for: a card or a list of
# moves longer than this is no help to a braider, and slow in a browser.
_MOST_CROSSINGS = 400


def _unit(info: Mapping[str, Any]):
    """The braid Braid Studio made, as its repeating unit — what is made
    once and repeated — and how many times it was.  None if it has no braid
    word, or one too long."""
    from braidpy.braid import Braid
    from braidpy.pure_braid import repeating_unit
    from braidpy.topology_catalog import braid_of

    braid = braid_of(info)
    if braid is None or not braid.generators:
        return None
    unit = tuple(repeating_unit(braid.generators))
    if len(unit) > _MOST_CROSSINGS:
        return None
    return Braid(unit, braid.n_strands), len(braid.generators) // len(unit)


def for_page(info: Mapping[str, Any]) -> Dict[str, Any]:
    """What Braid Studio shows of the other ways of making the braid it
    made: its repeating unit as moves on a kumihimo disk, and as a lace
    machine's punchcard.  Ashley's stand is searched for only when asked
    (:func:`sinnet_for_page`).

    Args:
        info: What :func:`braidpy.web.build` said of the braid.

    Returns:
        ``disk``: Braid Studio's description of the disk braid, and the
        moves; ``lace``: the card, the gears and how the bobbins are
        threaded.  Empty for a braid with no braid word, or too long.
    """
    from braidpy.bridges.disk import disk_moves
    from braidpy.bridges.lace import lace_card

    found = _unit(info)
    if found is None:
        return {}
    unit, repeats = found
    shown: Dict[str, Any] = {"crossings": len(unit.generators)}
    if 2 * unit.n_strands + 2 <= 32:
        moves = disk_moves(unit)
        # Made as many times as the braid shown repeats its unit.
        shown["disk"] = {
            "spec": {**moves.spec(), "cycles": repeats},
            "moves": moves.text(),
        }
    card = lace_card(unit)
    shown["lace"] = {
        "gears": card.n_gears,
        "steps": len(card.steps),
        "card": card.text(),
        # Named without building the machine, which needs networkx.
        "threading": " ".join(card.notches()),
    }
    return shown


def _alike(made: "Braid", wanted: "Braid") -> str:
    """How a sinnet's braid compares with the braid wanted, both one
    repeat: ``"same"``, the word itself from some crossing on;
    ``"reversed"``, the word read from its other end; ``"topology"``, only
    the topology the search matched.  Words are compared as written — the
    page has no sympy for braidpy's group equality."""
    got = [int(g) for g in made.generators if g]
    word = [int(g) for g in wanted.generators if g]
    for read, said in ((word, "same"), (word[::-1], "reversed")):
        if len(got) == len(read) and any(
            got == read[k:] + read[:k] for k in range(len(read))
        ):
            return said
    return "topology"


def sinnet_for_page(info: Mapping[str, Any], time_limit: float = 3.0) -> Dict[str, Any]:
    """A sinnet on Ashley's stand making the braid Braid Studio made, as
    the page shows it: searched for, for at most ``time_limit`` seconds.

    Args:
        info: What :func:`braidpy.web.build` said of the braid.
        time_limit: Seconds to search for.

    Returns:
        ``spec``: the sinnet, as Braid Studio makes it, or None if none was
        found, and ``alike``, how its braid compares
        (``"same"``, ``"reversed"`` or ``"topology"``); if none was found,
        ``exact``, the braid made one strand per space
        (:func:`~braidpy.bridges.ashley.ashley_moves`), and ``nearest`` and
        ``distance``, the nearest sinnet — another braid — and how far;
        ``complete``, whether every sinnet of up to as many spaces as
        strands was tried; ``tried``, how many were.
    """
    from braidpy.bridges.ashley import ashley_moves, ashley_sinnet, sinnet_spec

    found = _unit(info)
    if found is None:
        return {"spec": None, "complete": True, "tried": 0}
    unit, repeats = found
    search = ashley_sinnet(unit, time_limit=time_limit)
    # Made as many times as the braid shown repeats its unit.
    shown: Dict[str, Any] = {
        "spec": sinnet_spec(search.sinnet, cycles=repeats) if search.sinnet else None,
        "complete": search.complete,
        "tried": search.tried,
    }
    if search.sinnet is not None:
        shown["alike"] = _alike(search.sinnet.braid(1), unit)
    if search.sinnet is None:
        shown["exact"] = sinnet_spec(ashley_moves(unit), cycles=repeats)
        if search.nearest is not None:
            shown["nearest"] = sinnet_spec(search.nearest)
            shown["distance"] = round(search.distance, 2)
    return shown


__all__ = ["for_page", "sinnet_for_page"]
