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
}
