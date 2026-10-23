# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids the horn gear braiding machines of
:mod:`braidpy.horn_gear.examples` make, and the Jacquard lace machines
(:mod:`braidpy.horn_gear.jacquard`), as every catalogue lists its braids
(:mod:`braidpy.catalogue`).

Listing them loads nothing: a machine is only made, and the simulator and
networkx with it, when it is asked for.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from braidpy.catalogue import Entry

if TYPE_CHECKING:
    from braidpy.horn_gear.model import BraidingMachine

__all__ = ["CATALOGUE", "LACE", "LaceRing"]


def _example(name: str, **settings: Any) -> Callable[[], BraidingMachine]:
    """Makes the machine :mod:`braidpy.horn_gear.examples` names."""

    def make() -> BraidingMachine:
        from braidpy.horn_gear import examples

        return getattr(examples, name)(**settings)

    return make


# In the order to offer them; not the diamond braid, which is the tubular
# braid of 8 again, nor the mixed gears, which only show that gears may
# differ.
CATALOGUE: dict[str, Entry[BraidingMachine]] = {
    "flat_3": Entry("Flat braid, 3 carriers", _example("flat_braid_3")),
    "flat_4": Entry("Flat braid, 4 carriers", _example("flat_braid_4")),
    "flat_9": Entry(
        "Flat braid, 9 carriers on a single track", _example("flat_braid_9")
    ),
    "soutache_5": Entry("Soutache, 2 gears of 5", _example("soutache_braid")),
    "soutache_7": Entry(
        "Soutache, 2 gears of 7", _example("soutache_braid", n_slots=7)
    ),
    "princess": Entry("Princess, 5/6/5 gears, 8 carriers", _example("princess_braid")),
    "tubular_8": Entry("Tubular braid, 8 carriers", _example("tubular_braid_8")),
    "tubular_12": Entry("Tubular braid, 12 carriers", _example("tubular_braid_12")),
    "tubular_16": Entry("Tubular braid, 16 carriers", _example("tubular_braid_16")),
}


@dataclass(frozen=True)
class LaceRing:
    """A lace machine as data: its gears, its card — per step, whether each
    gear turns anticlockwise, then clockwise — and the notches threaded,
    every one if None.  Listed without making the machine, which needs
    networkx."""

    n_gears: int
    steps: tuple[tuple[tuple[bool, ...], tuple[bool, ...]], ...]
    threaded: tuple[int, ...] | None = None

    def machine(self) -> BraidingMachine:
        """The machine, its gears driven by the card."""
        from braidpy.horn_gear.jacquard import jacquard_lace_ring

        return jacquard_lace_ring(
            self.n_gears, list(self.steps), threaded=self.threaded
        )


def _ring(n_gears: int) -> Callable[[], LaceRing]:
    """A lace ring with every gear turning, a bobbin in every notch."""

    def make() -> LaceRing:
        ccw = tuple(g % 2 == 0 for g in range(n_gears))
        cw = tuple(g % 2 == 1 for g in range(n_gears))
        return LaceRing(n_gears, ((ccw, cw),))

    return make


def _card(braid: str) -> Callable[[], LaceRing]:
    """A lace ring driven by the punchcard for a braid of
    :data:`braidpy.braid_catalog.CATALOGUE`, its repeating unit
    (:func:`~braidpy.making.lace.lace_card`), threaded as the card says."""

    def make() -> LaceRing:
        from braidpy.braid import Braid
        from braidpy.braid_catalog import CATALOGUE as BRAIDS
        from braidpy.making.lace import lace_card
        from braidpy.pure_braid import repeating_unit

        made = BRAIDS[braid].make()
        unit = repeating_unit([int(g) for g in made.generators])
        card = lace_card(Braid(tuple(unit), made.n_strands))
        return LaceRing(card.n_gears, card.steps, tuple(card.threaded()))

    return make


# Jacquard lace machines, in the order to offer them: punchcards for braids
# of the braid catalogue, each a pass of the card a repeat of the braid,
# then a ring turning every gear, as a tubular braider does.
LACE: dict[str, Entry[LaceRing]] = {
    "lace_dutch": Entry(
        "Dutch braid of 3 (ABOK 2966), 4 gears", _card("inverted_flat3")
    ),
    "lace_plait": Entry(
        "Plait, or flat sinnet of 3 (ABOK 2965), 4 gears", _card("flat3")
    ),
    "lace_weave3": Entry("Weave of 3 (ABOK 2973), 4 gears", _card("weave3")),
    "lace_sinnet4": Entry(
        "Four-strand sinnet (ABOK 2974), 6 gears", _card("abok_2974")
    ),
    "lace_square4": Entry("Square sinnet of 4 (ABOK 2999), 6 gears", _card("square4")),
    "lace_flat6": Entry("Regular flat braid of 6, 8 gears", _card("regular_flat6")),
    "lace_tubular_8": Entry("Every gear turning, 8 gears and bobbins", _ring(8)),
}
