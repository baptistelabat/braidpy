# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as moves on a kumihimo disk (a mobidai).

A mobidai's move takes one strand from a slot to another, the short way
round, lifted over every strand it passes (:mod:`braidpy.mobidai`).  The
strands are kept two slots apart — strand ``k`` from slot ``2k + 3`` — so
that every strand has an empty slot either side of it, and each crossing
is three moves:

- one of the two strands crossing is lifted over the other, and over every
  strand between them, into the empty slot beyond it;
- the other moves into the place it left;
- the lifted strand settles into the other's old place.

Every strand is then back two slots from the next, and the disk ready for
the next crossing.  The two strands need not be neighbours: a band letter
``a_ts`` (:mod:`braidpy.band_canonical_form`), strands ``t`` and ``s``
crossing in front of those between, is three moves however far apart they
are, where in crossings of neighbours it is ``2(t - s) - 1`` of them.  The
braid is made in band letters where that takes fewer — a disk braid, its
strands carried across the disk: Kongo gumi's 81 crossings, 243 moves so,
are 43 letters, 129 moves — and as its ring program's crossings of
neighbours (:mod:`braidpy.ring_program`) where not, as a machine's braid.
A 32-slot disk takes up to 15 strands this way.  None passes the seam
between the last slot and the first: that would twist the braid, which is
still a braid and can be shorter to make, but from a braid word the
strands are in a row, and keeping them so makes the word itself.  Shorter
moves, over the seam, are for later.

:func:`disk_braid` reads the braid back as braidpy reads any mobidai's
(:func:`~braidpy.take_off.mobidai_steps`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from braidpy.band_canonical_form import band_letters, band_word
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

    # The fewer letters of two: the band normal form, far shorter for a
    # braid of strands carried across the disk; or the word as it stands,
    # each run spelling a band letter read as one.
    letters = min(
        band_word(braid.generators, n), band_letters(braid.generators), key=len
    )
    if len(letters) >= len(braid.generators):
        # No shorter: the ring program's crossings, each of neighbours,
        # a_{i+1,i}.
        letters = [
            (swap.place + 2, swap.place + 1)
            if swap.sign > 0
            else (swap.place + 1, swap.place + 2)
            for swap in from_braid(braid).swaps()
        ]
    moves: list[tuple[int, int]] = []
    for first, second in letters:
        low, high = slot(min(first, second) - 1), slot(max(first, second) - 1)
        if first > second:
            # The higher strand lifted over the rest, into the slot below
            # the lower.
            moves += [(high, low - 1), (low, high), (low - 1, low)]
        else:
            # The lower strand lifted over the rest, above the higher.
            moves += [(low, high + 1), (high, low), (high + 1, high)]
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
