# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as moves on a kumihimo disk (a mobidai).

A mobidai's move takes one strand from a slot to another, the short way
round, lifted over every strand it passes (:mod:`braidpy.mobidai`).  Each
crossing of the braid's ring program (:mod:`braidpy.ring_program`) becomes
three moves, the strands kept two slots apart — strand ``k`` from slot
``2k + 3`` — so that every strand has an empty slot either side of it:

- the strand lifted goes over its neighbour, into the empty slot beyond it:
  the crossing;
- the neighbour moves into the place it left, crossing nobody;
- the lifted strand settles into the neighbour's old place, crossing nobody.

Every strand is then back two slots from the next, and the disk ready for
the next crossing.  A 32-slot disk takes up to 15 strands this way.  None
passes the seam between the last slot and the first: that would twist the
braid, which is still a braid and can be shorter to make, but from a braid
word the strands are in a row, and keeping them so makes the word itself
(:mod:`braidpy.ring_program`).  Shorter moves, over the seam, are for later.

:func:`disk_braid` reads the braid back as braidpy reads any mobidai's
(:func:`~braidpy.take_off.mobidai_steps`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from braidpy.braid import Braid
from braidpy.ring_program import from_braid

__all__ = ["DiskMoves", "disk_braid", "disk_moves"]


@dataclass(frozen=True)
class DiskMoves:
    """A braid as a kumihimo disk makes it.

    Args:
        n_slots: Slots round the disk.
        slots: The slot each strand starts in, 1-based.
        moves: The moves, each from a slot to another, the short way round.
    """

    n_slots: int
    slots: tuple[int, ...]
    moves: tuple[tuple[int, int], ...]

    def config(self):
        """The disk as braidpy's mobidai describes it.

        Returns:
            A :class:`~braidpy.mobidai.MobidaiConfig`, one cycle being the
            whole braid.
        """
        from braidpy.mobidai import MobidaiConfig, Move, Strand
        from braidpy.utils import PALETTE

        return MobidaiConfig(
            strands=[
                Strand(PALETTE[k % len(PALETTE)], slot, k)
                for k, slot in enumerate(self.slots)
            ],
            moves=[Move(a, b) for a, b in self.moves],
            n_shift_after_cycle=0,
            n_slots=self.n_slots,
        )

    def text(self) -> str:
        """The moves as a braider writes them: ``from>to``, in order."""
        return ", ".join(f"{a}>{b}" for a, b in self.moves)

    def spec(self) -> dict[str, Any]:
        """The disk as Braid Studio makes your own disk braid
        (:func:`braidpy.web.build`), once through."""
        return {
            "source": "mobidai",
            "name": "custom",
            "n_slots": self.n_slots,
            "slots": " ".join(str(s) for s in self.slots),
            "moves": self.text(),
            "cycles": 1,
        }


def disk_moves(braid: Braid, n_slots: int = 32) -> DiskMoves:
    """A braid as moves on a kumihimo disk; see the module.

    Args:
        braid: The braid.
        n_slots: Slots round the disk.

    Returns:
        The moves.  :func:`disk_braid` reads back the same braid, exactly.

    Raises:
        ValueError: If the disk has too few slots for the strands, two apart
            with room either side.
    """
    n = braid.n_strands
    if 2 * n + 2 > n_slots:
        raise ValueError(
            f"{n} strands, two slots apart, need a disk of {2 * n + 2} slots "
            f"at least: this one has {n_slots}."
        )

    def slot(place: int) -> int:
        return 2 * place + 3

    moves: list[tuple[int, int]] = []
    for swap in from_braid(braid).swaps():
        left, right = slot(swap.place), slot(swap.place + 1)
        if swap.sign > 0:
            # The right strand lifted over the left, into the slot beyond it.
            moves += [(right, left - 1), (left, right), (left - 1, left)]
        else:
            # The left strand lifted over the right.
            moves += [(left, right + 1), (right, left), (right + 1, right)]
    return DiskMoves(n_slots, tuple(slot(k) for k in range(n)), tuple(moves))


def disk_braid(moves: DiskMoves) -> Braid:
    """The braid a disk's moves make, read as braidpy reads any mobidai.

    Args:
        moves: The moves.

    Returns:
        The braid.
    """
    from braidpy.annulus_braid import solid_word
    from braidpy.take_off import disk_annular_word, mobidai_steps

    start, steps = mobidai_steps(moves.config(), n_cycles=1, drift=0)
    annular, n = disk_annular_word(start, steps, moves.n_slots, clockwise=True)
    return Braid(tuple(solid_word(annular, n)), n)
