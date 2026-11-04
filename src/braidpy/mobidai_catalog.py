# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
mobidai_catalog.py
==================

Kumihimo braids transcribed from *Bracelets Kumihimo, technique des bracelets
japonais* by Agnès Delage-Calvet, and braids shared by Richard Buenger in the
Kumihimo group on Facebook (each entry says which).

Each entry carries everything a :class:`~braidpy.mobidai.Mobidai` needs: how
many slots the disk has, which colour starts in which slot, the moves of one
cycle, and how far the disk is turned before the cycle repeats.  Call
:meth:`CataloguedMobidai.to_config` to run one.  :data:`CATALOGUE` lists
them, as every catalogue does (:mod:`braidpy.catalogue`).
"""

from __future__ import annotations

from dataclasses import dataclass

from braidpy.catalogue import Entry

__all__ = ["CATALOGUE", "CataloguedBraid", "CataloguedMobidai"]


@dataclass(frozen=True)
class CataloguedMobidai:
    """One disk braid from the book, ready to run on a mobidai.

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
    initial_slots: tuple[tuple[int, str], ...]
    moves: tuple[tuple[int, int], ...]
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


KONGO_8 = CataloguedMobidai(
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
    # One cycle.  It brings every pair back one slot round — 32/1 to 31/32 —
    # and the next is the same four moves from there: the book's next two,
    # (16, 30) and (32, 14), are this cycle's first two made a slot back.
    moves=((1, 15), (17, 31), (25, 7), (9, 23)),
)

SEVEN_ON_EIGHT = CataloguedMobidai(
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

TWELVE_STRANDS = CataloguedMobidai(
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

SIXTEEN_STRANDS = CataloguedMobidai(
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

# Shared by Richard Buenger in the Kumihimo group on Facebook, as Braid
# Studio links: the slots, moves and colours he set up there.
BUENGER = "Richard Buenger, Kumihimo group (Facebook)"

EDO_YATSU = CataloguedMobidai(
    name="edo yatsu",
    n_slots=32,
    initial_slots=(
        (32, "#ff0000"),
        (1, "#ffbf00"),
        (17, "#80ff00"),
        (16, "#00ff40"),
        (25, "#00ffff"),
        (24, "#0040ff"),
        (8, "#8000ff"),
        (9, "#ff00bf"),
    ),
    moves=(
        (32, 7),
        (8, 15),
        (16, 23),
        (24, 32),
        (7, 8),
        (15, 16),
        (23, 24),
        (1, 26),
        (25, 18),
        (17, 10),
        (9, 1),
        (26, 25),
        (18, 17),
        (10, 9),
    ),
    source=BUENGER,
)

NAIKI = CataloguedMobidai(
    name="naiki",
    n_slots=32,
    initial_slots=(
        (32, "#ff0000"),
        (1, "#ff6000"),
        (4, "#ffbf00"),
        (5, "#dfff00"),
        (12, "#80ff00"),
        (13, "#20ff00"),
        (17, "#00ff40"),
        (16, "#00ff9f"),
        (20, "#00ffff"),
        (21, "#009fff"),
        (25, "#0040ff"),
        (24, "#2000ff"),
        (28, "#8000ff"),
        (29, "#df00ff"),
        (8, "#ff00bf"),
        (9, "#ff0060"),
    ),
    moves=(
        (32, 3),
        (4, 7),
        (8, 11),
        (12, 15),
        (16, 19),
        (20, 23),
        (24, 27),
        (28, 32),
        (3, 4),
        (7, 8),
        (11, 12),
        (15, 16),
        (19, 20),
        (23, 24),
        (27, 28),
        (1, 30),
        (29, 26),
        (25, 22),
        (21, 18),
        (17, 14),
        (13, 10),
        (9, 6),
        (5, 1),
        (30, 29),
        (26, 25),
        (22, 21),
        (18, 17),
        (14, 13),
        (10, 9),
        (6, 5),
    ),
    source=BUENGER,
)

HIRA_NAIKI = CataloguedMobidai(
    name="hira-naiki",
    n_slots=32,
    initial_slots=(
        (31, "#e41a1c"),
        (2, "#e41a1c"),
        (4, "#ffffff"),
        (5, "#ffffff"),
        (8, "#ffffff"),
        (9, "#ffffff"),
        (12, "#ffffff"),
        (13, "#ffffff"),
        (16, "#e41a1c"),
        (17, "#e41a1c"),
        (20, "#ffffff"),
        (21, "#ffffff"),
        (24, "#ffffff"),
        (25, "#ffffff"),
        (28, "#ffffff"),
        (29, "#ffffff"),
    ),
    moves=(
        (17, 32),
        (16, 1),
        (2, 16),
        (31, 17),
        (1, 2),
        (32, 31),
        (28, 3),
        (12, 19),
        (4, 7),
        (20, 23),
        (3, 4),
        (19, 20),
        (8, 12),
        (24, 28),
        (7, 8),
        (23, 24),
        (29, 26),
        (13, 10),
        (25, 22),
        (26, 25),
        (9, 6),
        (10, 9),
        (5, 29),
        (6, 5),
        (21, 13),
        (22, 21),
    ),
    source=BUENGER,
)

UNERI_MARU_GENJI = CataloguedMobidai(
    name="uneri-maru-genji",
    n_slots=32,
    initial_slots=(
        (31, "#66c2a5"),
        (2, "#66c2a5"),
        (3, "#4daf4a"),
        (5, "#ffffff"),
        (6, "#ffffff"),
        (8, "#ffffff"),
        (9, "#ffffff"),
        (11, "#ffffff"),
        (12, "#ffffff"),
        (14, "#377eb8"),
        (15, "#555555"),
        (18, "#555555"),
        (19, "#377eb8"),
        (21, "#ffffff"),
        (22, "#ffffff"),
        (24, "#ffffff"),
        (25, "#ffffff"),
        (27, "#ffffff"),
        (28, "#ffffff"),
        (30, "#4daf4a"),
    ),
    moves=(
        (19, 32),
        (14, 1),
        (3, 16),
        (30, 17),
        (22, 4),
        (6, 20),
        (21, 22),
        (20, 21),
        (5, 6),
        (4, 5),
        (25, 7),
        (9, 23),
        (24, 25),
        (23, 24),
        (8, 9),
        (7, 8),
        (28, 10),
        (12, 26),
        (27, 28),
        (26, 27),
        (11, 12),
        (10, 11),
        (15, 14),
        (16, 15),
        (18, 19),
        (17, 18),
        (2, 3),
        (1, 2),
        (31, 30),
        (32, 31),
    ),
    source=BUENGER,
)

# Other braids, from pictures found on the internet, not transcribed yet:
# https://i.pinimg.com/736x/56/49/d5/5649d5a7781677b7fb61538bc0a7ccb5.jpg
# https://i.pinimg.com/736x/2c/16/ba/2c16bacb81b1b4a7bdda9e2f24e5b6eb.jpg

# Its name until it said what kind of braid it is.
CataloguedBraid = CataloguedMobidai


def _entry(braid: CataloguedMobidai) -> Entry[CataloguedMobidai]:
    return Entry(
        title=braid.name[0].upper() + braid.name[1:],
        make=lambda: braid,
        reference=braid.source,
    )


CATALOGUE: dict[str, Entry[CataloguedMobidai]] = {
    "KONGO_8": _entry(KONGO_8),
    "SEVEN_ON_EIGHT": _entry(SEVEN_ON_EIGHT),
    "TWELVE_STRANDS": _entry(TWELVE_STRANDS),
    "SIXTEEN_STRANDS": _entry(SIXTEEN_STRANDS),
    "EDO_YATSU": _entry(EDO_YATSU),
    "NAIKI": _entry(NAIKI),
    "HIRA_NAIKI": _entry(HIRA_NAIKI),
    "UNERI_MARU_GENJI": _entry(UNERI_MARU_GENJI),
}
