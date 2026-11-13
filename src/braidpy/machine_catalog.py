# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids horn gear braiding machines make, and the Jacquard lace
machines (:mod:`braidpy.horn_gear.jacquard`), as every catalogue lists its
braids (:mod:`braidpy.catalogue`).

A horn gear machine is written as its graph, as a machine of your own is
(:func:`~braidpy.horn_gear.described.machine_from_graph`): the gears that
mesh, where it feeds axial yarns, and the carriers it starts with where it
does not load itself.  The machines that braid several bands at once are
still built by :mod:`braidpy.horn_gear.multiband`, as their line folds
round and their bands' colours are more than a graph says yet.

Listing them loads nothing: a machine is only made, and the simulator and
networkx with it, when it is asked for.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from braidpy.catalogue import Entry, Link

if TYPE_CHECKING:
    from braidpy.horn_gear.model import BraidingMachine

__all__ = ["CATALOGUE", "LACE", "LaceRing"]


def _multiband(name: str, **settings: Any) -> Callable[[], BraidingMachine]:
    """Makes the machine :mod:`braidpy.horn_gear.multiband` names."""

    def make() -> BraidingMachine:
        from braidpy.horn_gear import multiband

        return getattr(multiband, name)(**settings)

    return make


def _graph(
    graph: str, n_slots: int = 4, axials: str = "", loading: str = ""
) -> Callable[[], BraidingMachine]:
    """Makes the machine its graph describes
    (:func:`~braidpy.horn_gear.described.machine_from_graph`)."""

    def make() -> BraidingMachine:
        from braidpy.horn_gear.described import machine_from_graph

        return machine_from_graph(graph, n_slots, axials=axials, loading=loading)

    return make


# The tubular braid of 16 carriers, two to a gear on alternate slots.
_RING_8 = "A-B B-C C-D D-E E-F F-G G-H H-A"
_RING_8_LOADING = "A:3 C:1 E:1 G:1 H:0 F:0 D:0 B:0 A:1 G:3 E:3 C:3 B:2 D:2 F:2 H:2"

# In the order to offer them.  Each is the machine of
# braidpy.horn_gear.examples of the same name, written as its graph, laying
# its carriers where that one does; but for the ring of four gears, whose
# contacts the graph spreads round each gear where that one puts them side
# by side: another machine, making the same braid.
CATALOGUE: dict[str, Entry[BraidingMachine]] = {
    "flat_3": Entry("Flat braid, 3 carriers", _graph("A-B", 3)),
    "flat_4": Entry("Flat braid, 4 carriers", _graph("A-B")),
    "flat_9": Entry(
        "Flat braid, 9 carriers on a single track",
        _graph("A-B:4 B-C:4 C-D", 5, loading="A:0 A:2 A:4 B:2 B:3 C:2 C:1 D:2 D:4"),
    ),
    # The cord of a soutache, an axial yarn up each gear.
    "soutache_5": Entry("Soutache, 2 gears of 5", _graph("A-B", 5, axials="A B")),
    "soutache_7": Entry("Soutache, 2 gears of 7", _graph("A-B", 7, axials="A B")),
    "princess": Entry(
        "Princess, 5/6/5 gears, 8 carriers", _graph("A-B:6 B-C", 5, axials="B")
    ),
    "tubular_8": Entry("Tubular braid, 8 carriers", _graph("A-B B-C C-D D-A")),
    "tubular_12": Entry(
        "Tubular braid, 12 carriers",
        _graph(
            "A-B B-C C-D D-E E-F F-A",
            loading="A:3 C:1 E:1 F:0 D:0 B:0 A:1 E:3 C:3 B:2 D:2 F:2",
        ),
    ),
    "tubular_16": Entry(
        "Tubular braid, 16 carriers", _graph(_RING_8, loading=_RING_8_LOADING)
    ),
    # The tubular braid of 16 again, round an axial yarn up each gear.
    "triaxial_16": Entry(
        "Triaxial braid, 16 carriers round 8 axial yarns",
        _graph(_RING_8, axials="A B C D E F G H", loading=_RING_8_LOADING),
        (
            Link(
                "J. H. van Ravenhorst, Design tools for circular overbraiding of "
                "complex mandrels (thesis)",
                "article",
                "https://ris.utwente.nl/ws/portalfiles/portal/46645249/"
                "PhD_thesis_Johan_van_Ravenhorst.pdf",
            ),
        ),
    ),
    # Lines braiding several bands at once, split gears between them: the
    # smallest, two plaits on three gears, then the three-band machine of the
    # Atelier de Tressage whole and its bands one at a time.  A band keeps the
    # whole machine's gear names and slot numbering, so a loading reads the
    # same there as here.
    "twin_plait": Entry(
        "Two plaits at once: 3/6/3 gears, the middle one split",
        _multiband("twin_plait"),
    ),
    "multiband_10_15_10": Entry(
        "Three-band machine, 10-15-10 carriers",
        _multiband("multiband_10_15_10"),
        (
            Link(
                "L'Atelier de Tressage: la tresse plate",
                "page",
                "https://www.atelierdetressage.paris/tresse-plate/",
            ),
        ),
    ),
    "multiband_band_0": Entry(
        "Three-band machine: left band alone, gears G0-G4",
        _multiband("multiband_band", band=0),
    ),
    "multiband_band_1": Entry(
        "Three-band machine: middle band alone, gears G4-G11",
        _multiband("multiband_band", band=1),
    ),
    "multiband_band_2": Entry(
        "Three-band machine: right band alone, gears G11-G15",
        _multiband("multiband_band", band=2),
    ),
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
