# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids the horn gear braiding machines of
:mod:`braidpy.horn_gear.examples` make, as every catalogue lists its braids
(:mod:`braidpy.catalogue`).

Listing them loads nothing: a machine is only made, and the simulator and
networkx with it, when it is asked for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict

from braidpy.catalogue import Entry

if TYPE_CHECKING:
    from braidpy.horn_gear.model import BraidingMachine

__all__ = ["CATALOGUE"]


def _switched(name: str, **settings: Any) -> Callable[[], BraidingMachine]:
    """Makes the machine :mod:`braidpy.horn_gear.switch` names."""

    def make() -> BraidingMachine:
        from braidpy.horn_gear import switch

        return getattr(switch, name)(**settings)

    return make


def _example(name: str, **settings: Any) -> Callable[[], BraidingMachine]:
    """Makes the machine :mod:`braidpy.horn_gear.examples` names."""

    def make() -> BraidingMachine:
        from braidpy.horn_gear import examples

        return getattr(examples, name)(**settings)

    return make


# In the order to offer them; not the diamond braid, which is the tubular
# braid of 8 again, nor the mixed gears, which only show that gears may
# differ.
CATALOGUE: Dict[str, Entry[BraidingMachine]] = {
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
    # The three-band line's bands, one at a time.  A band keeps the whole
    # machine's gear names and slot numbering, so a loading reads the same
    # here as there.
    #
    # The whole line is not offered: its carriers only come back to where
    # they started after 15120 steps, sixty times the next machine here, and
    # the braid made over that is a word of some 120000 crossings -- minutes
    # to work out before the page can draw anything.  It is still
    # braidpy.horn_gear.switch.multiband_10_15_10 for Python to make.
    "multiband_band_0": Entry(
        "Three-band machine: left band alone, gears G0-G4",
        _switched("multiband_band", band=0),
    ),
    "multiband_band_1": Entry(
        "Three-band machine: middle band alone, gears G4-G11",
        _switched("multiband_band", band=1),
    ),
    "multiband_band_2": Entry(
        "Three-band machine: right band alone, gears G11-G15",
        _switched("multiband_band", band=2),
    ),
}
