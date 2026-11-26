# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""How to make a braid, by hand or on a machine: each through a
:class:`~braidpy.ring_program.RingProgram`, and each checked by reading the
braid back off what it made.  See ``docs/source/making.md``.

- :mod:`braidpy.making.lace`: the Jacquard lace machine's punchcard;
- :mod:`braidpy.making.disk`: moves on a kumihimo disk;
- :mod:`braidpy.making.ashley`: a sinnet on Ashley's stand, by searching.
"""

from collections.abc import Mapping
from typing import Any

# Longest repeating unit the page is shown how to make: a card or a list of
# moves longer than this is no help to a braider, and slow in a browser.
_MOST_CROSSINGS = 400
# The core a tube's lace card is made round, in Braid Studio
# (braidpy.web._settings.CORE_KINDS): one of yarn, down the ring's hole.
TUBE_CORE = "yarn"


def _unit(info: Mapping[str, Any]):
    """The braid Braid Studio made, as its repeating unit — what is made
    once and repeated — and how many times it was.  None if it has no braid
    word, or one too long."""
    from braidpy.braid import Braid
    from braidpy.pure_braid import repeating_unit
    from braidpy.topology_catalogue import braid_of

    braid = braid_of(info)
    if braid is None or not braid.generators:
        return None
    unit = tuple(repeating_unit(braid.generators))
    if len(unit) > _MOST_CROSSINGS:
        return None
    return Braid(unit, braid.n_strands), len(braid.generators) // len(unit)


def _passes(source: str, repeats: int) -> int:
    """How many times a link may ask for the unit to be made again.

    As many as the braid shown repeats it, but no more than that source
    will take: the bounds are the page's own (:mod:`braidpy.web._settings`),
    and a link asking past them is refused rather than drawn.  Fewer passes
    make less of the braid, which a visitor can put back up by hand.

    Args:
        source: Which source the link is for.
        repeats: How many times the braid shown repeats its unit.

    Returns:
        The passes to ask for.
    """
    from braidpy.web._settings import Lace, Mobidai, Sinnet

    allowed = {"mobidai": Mobidai.cycles, "lace": Lace.cycles, "sinnet": Sinnet.cycles}
    cycles = allowed[source]
    return max(cycles.low, min(repeats, cycles.high))


def for_page(info: Mapping[str, Any]) -> dict[str, Any]:
    """What Braid Studio shows of the other ways of making the braid it
    made: its repeating unit as moves on a kumihimo disk, and as a lace
    machine's punchcard.  Ashley's stand is searched for only when asked
    (:func:`sinnet_for_page`).

    Args:
        info: What :func:`braidpy.web.build` said of the braid.

    Returns:
        ``disk``: Braid Studio's description of the disk braid, and the
        moves; ``lace``: the card, the gears, how the bobbins are threaded
        and Braid Studio's description of the lace machine, and whether it
        makes the braid as a tube — for a braid made round a core, its
        strands going round across the ring's seam, its card's unit the
        shortest stretch that, repeated, makes it (:func:`_tube_card`).
        Empty for a braid with no braid word, or too long.
    """
    from braidpy.making.disk import disk_moves
    from braidpy.making.lace import card_conjugate, lace_card

    found = _unit(info)
    if found is None:
        return {}
    unit, repeats = found
    # Fewer crossings, fewer moves: the unit as short as is found.
    unit = unit.shortened()
    shown: dict[str, Any] = {"crossings": len(unit.generators)}
    if 2 * unit.n_strands + 2 <= 32:
        moves = disk_moves(unit)
        # Made as many times as the braid shown repeats its unit, as far
        # as the disk will take (:func:`_passes`).
        shown["disk"] = {
            "spec": {**moves.spec(), "cycles": _passes("mobidai", repeats)},
            "moves": moves.text(),
        }
    tube = _tube_card(info)
    if tube is not None:
        card, repeats = tube
    else:
        # The card repeats the unit: a conjugate of it is the same braid
        # once repeated, and may take far fewer steps (card_conjugate).
        card = lace_card(card_conjugate(unit))
    spec = card.spec(cycles=_passes("lace", repeats))
    if tube is not None:
        # Round a core, so that the tube is seen as one.
        spec["core"] = TUBE_CORE
    shown["lace"] = {
        "gears": card.n_gears,
        "steps": len(card.steps),
        "card": card.text(),
        # Named without building the machine, which needs networkx.
        "threading": " ".join(card.notches()),
        # Made as many times as the braid shown repeats its unit, as far
        # as the machine will take (:func:`_passes`).
        "spec": spec,
        "tube": tube is not None,
    }
    return shown


def _tube_card(info: Mapping[str, Any]):
    """For a braid made round a core, as a tube — on a ring of gears, or a
    ring word — its lace card made as a tube
    (:func:`~braidpy.making.lace.ring_card`), and how many times the braid
    shown makes its card's unit; None for any other braid, or one no card
    makes so."""
    from braidpy.making.lace import ring_card

    if not info.get("ring_unit"):
        return None
    moves = [int(g) for g in str(info["ring_unit"]).split()]
    if len(moves) > _MOST_CROSSINGS:
        return None
    try:
        card = ring_card(moves, int(info["ring_strands"]))
    except ValueError:
        return None
    return card, int(info["ring_repeats"])


def sinnet_for_page(
    info: Mapping[str, Any], time_limit_s: float = 3.0
) -> dict[str, Any]:
    """A sinnet on Ashley's stand making the braid Braid Studio made, as
    the page shows it: searched for, for at most ``time_limit_s`` seconds.

    Args:
        info: What :func:`braidpy.web.build` said of the braid.
        time_limit_s: Seconds to search for.

    Returns:
        ``spec``: the sinnet, as Braid Studio makes it, or None if none was
        found, ``exact`` then being the braid made one strand per space
        (:func:`~braidpy.making.ashley.ashley_moves`), which always makes
        it; ``complete``, whether every sinnet of up to as many spaces as
        strands was tried; ``tried``, how many were.
    """
    from braidpy.making.ashley import ashley_moves, ashley_sinnet, sinnet_spec

    found = _unit(info)
    if found is None:
        return {"spec": None, "complete": True, "tried": 0}
    unit, repeats = found
    search = ashley_sinnet(unit, time_limit_s=time_limit_s)
    # Made as many times as the braid shown repeats its unit, as far as the
    # stand will take (:func:`_passes`).
    passes = _passes("sinnet", repeats)
    shown: dict[str, Any] = {
        "spec": sinnet_spec(search.sinnet, cycles=passes) if search.sinnet else None,
        "complete": search.complete,
        "tried": search.tried,
    }
    if search.sinnet is None:
        shown["exact"] = sinnet_spec(ashley_moves(unit), cycles=passes)
    return shown


__all__ = ["for_page", "sinnet_for_page"]
