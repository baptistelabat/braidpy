# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What is known of a braid, for the page's info card: its word and crossings,
its permutation, how many times it is repeated before it is pure, and its
Garside normal form."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from braidpy.web._types import Info


def _braid_info(word: Sequence[int], n_strands: int) -> Info:
    """What is known of a flat braid word: its crossings and permutation."""
    from braidpy.braid import Braid
    from braidpy.pure_braid import closing_repeats, components

    word = [int(g) for g in word]
    info: Info = {
        "word": " ".join(str(g) for g in word),
        "crossings": len(word),
        "exponent_sum": int(sum(np.sign(word))),
    }
    if word:
        braid = Braid(word, n_strands)
        info["permutation"] = [int(p) for p in braid.perm()]
        info["pure"] = bool(braid.is_pure())
        info["pure_after"] = closing_repeats(braid, limit=None)
        info["components"] = components(braid)
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
                "full_twists": math.floor((least + most) / 4 + 0.5),
            }
    return info


def _unit(info: Info, word: Sequence[int], n_strands: int, repeated: str) -> Info:
    """Says in ``info`` how many of the braid's unit — its word repeated, or
    its moves' cycle, as ``repeated`` names it — make a pure braid."""
    from braidpy.braid import Braid
    from braidpy.pure_braid import closing_repeats

    word = [int(g) for g in word]
    info["pure_after"] = (
        closing_repeats(Braid(word, n_strands), limit=None) if word else 1
    )
    info["repeated"] = repeated
    return info


def _disk_unit(
    info: Info,
    cycles: Callable[[int], tuple[Any, Any, int]],
    clockwise: bool,
    repeated: str = "cycle",
) -> Info:
    """:func:`_unit` for a disk braid, whose ``cycles(k)`` are the start,
    steps and slots of ``k`` cycles of its moves.  A braid that creeps round the disk
    from cycle to cycle, as kongo gumi does, is not its first cycle repeated:
    its cycles are counted until the braid is pure, up to
    :data:`_MOST_CYCLES`."""
    from braidpy.annulus_braid import solid_word
    from braidpy.braid import Braid
    from braidpy.pure_braid import closing_repeats
    from braidpy.take_off import disk_annular_word

    def repeats(k: int) -> int | None:
        """How many of ``k`` cycles make a pure braid."""
        start, steps, n_slots = cycles(k)
        annular, n = disk_annular_word(start, steps, n_slots, clockwise=clockwise)
        word = solid_word(annular, n)
        return closing_repeats(Braid(word, n), limit=None) if word else 1

    k: int | None = repeats(1)
    if k and k > 1 and repeats(k) != 1:
        k = next((k for k in range(2, _MOST_CYCLES + 1) if repeats(k) == 1), None)
    info["pure_after"] = k
    info["repeated"] = repeated
    return info


# Cycles counted, at most, to find when a creeping disk braid is pure.
_MOST_CYCLES = 64


def _disk_info(start, steps, n_slots: int, clockwise: bool) -> Info:
    """A disk braid's word, read round the ring and with the middle solid."""
    from braidpy.annulus_braid import solid_word
    from braidpy.take_off import disk_annular_word

    annular, n = disk_annular_word(start, steps, n_slots, clockwise=clockwise)
    info = _braid_info(solid_word(annular, n), n)
    info["annular_word"] = " ".join(str(g) for g in annular)
    return info
