# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
mobidai_catalog.py
==================

Kumihimo braids transcribed from *Bracelets Kumihimo, technique des bracelets
japonais* by Agnès Delage-Calvet.

Each entry carries everything a :class:`~braidpy.mobidai.Mobidai` needs: how
many slots the disk has, which colour starts in which slot, the moves of one
cycle, and how far the disk is turned before the cycle repeats.  Call
:meth:`CataloguedBraid.to_config` to run one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

__all__ = ["CATALOGUE", "CataloguedBraid"]


@dataclass(frozen=True)
class CataloguedBraid:
    """One braid from the book, ready to run.

    Args:
        name: How the braid is referred to here.
        n_slots: Slots round the disk.
        initial_slots: ``(slot, colour)`` for each strand at the start.
        moves: ``(from_slot, to_slot)`` in the order they are made, for one
            cycle.
        n_shift_after_cycle: How far the disk turns before repeating; some
            braids are a cycle of moves plus a rotation.
        source: Where in the book it comes from.
    """

    name: str
    n_slots: int
    initial_slots: Tuple[Tuple[int, str], ...]
    moves: Tuple[Tuple[int, int], ...]
    n_shift_after_cycle: int = 0
    source: str = "Delage-Calvet, Bracelets Kumihimo"

    @property
    def n_strands(self) -> int:
        """How many strands are threaded."""
        return len(self.initial_slots)

    def to_config(self, **overrides):
        """A :class:`~braidpy.mobidai.MobidaiConfig` for this braid.

        Args:
            **overrides: Passed to the config, to vary a braid without
                editing the catalogue.

        Returns:
            MobidaiConfig: Ready to hand to :class:`~braidpy.mobidai.Mobidai`.
        """
        from .mobidai import MobidaiConfig, Move, Strand

        settings = {
            "n_slots": self.n_slots,
            "strands": [Strand(colour, slot) for slot, colour in self.initial_slots],
            "moves": [Move(source, target) for source, target in self.moves],
            "n_shift_after_cycle": self.n_shift_after_cycle,
        }
        settings.update(overrides)
        return MobidaiConfig(**settings)


KONGO_8 = CataloguedBraid(
    name="kongo gumi, 8 strands",
    n_slots=32,
    initial_slots=(
        (32, "red"),
        (1, "red"),
        (17, "red"),
        (16, "red"),
        (25, "green"),
        (24, "green"),
        (8, "green"),
        (9, "green"),
    ),
    moves=((1, 15), (17, 31), (25, 7), (9, 23), (16, 30), (32, 14)),
)

SEVEN_ON_EIGHT = CataloguedBraid(
    name="7 strands on a small disk",
    n_slots=8,
    initial_slots=(
        (1, "red"),
        (2, "yellow"),
        (3, "purple"),
        (4, "red"),
        (5, "green"),
        (6, "orange"),
        (7, "blue"),
    ),
    moves=((3, 0),),
    n_shift_after_cycle=-3,
)

TWELVE_STRANDS = CataloguedBraid(
    name="12 strands",
    n_slots=32,
    initial_slots=(
        (1, "yellow"),
        (5, "pink"),
        (6, "pink"),
        (17, "pink"),
        (21, "pink"),
        (22, "pink"),
        (27, "pink"),
        (11, "blue"),
        (12, "red"),
        (16, "purple"),
        (28, "green"),
        (32, "cyan"),
    ),
    moves=((1, 15), (17, 31), (28, 10), (12, 26), (22, 4), (6, 20)),
)

SIXTEEN_STRANDS = CataloguedBraid(
    name="16 strands",
    n_slots=32,
    initial_slots=(
        (32, "green"),
        (1, "red"),
        (17, "green"),
        (16, "green"),
        (25, "red"),
        (24, "green"),
        (8, "red"),
        (9, "red"),
        (4, "red"),
        (5, "red"),
        (12, "red"),
        (13, "red"),
        (20, "green"),
        (21, "green"),
        (28, "red"),
        (29, "red"),
    ),
    moves=((1, 15), (17, 31), (29, 11), (13, 27), (25, 7), (9, 23), (21, 3), (5, 19)),
)

CATALOGUE: Dict[str, CataloguedBraid] = {
    braid.name: braid
    for braid in (KONGO_8, SEVEN_ON_EIGHT, TWELVE_STRANDS, SIXTEEN_STRANDS)
}
