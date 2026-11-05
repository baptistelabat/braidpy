# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A line of horn gears that braids several bands at once.

A line of gears braids **one** band however long it is: every interior gear
has two contacts, so a carrier entering by one leaves by the other and walks
the whole line.  A band needs a gear at each end that turns its carriers
back, and that gear needs an **odd** number of slots: an even one returns a
carrier to the strand it came in on and breaks the band into short tracks that
fill only part of it (see :func:`~braidpy.horn_gear.examples.flat_braid_9`).

Where two bands meet, one gear turns the carriers of both back.  It is a
**split gear**: two gears on one axis, turning together, one for each band,
with their horns between each other's.  A six-horn split gear gives each band
three: an odd turning gear for each, and the two never share a horn.  Each
half meets only its own band's neighbour, so a carrier can never cross into
the other band, and the half that is not at a contact is always a third of a
pitch away from it.

It is modelled as two :class:`~braidpy.horn_gear.model.HornGear` of three
slots at the same centre, drawn as large as the six-horn gear they make.  Each
turns one of its own slots a step, as every gear does, which is two horns of
the whole gear: the bands see three-slot turning gears, which is what the
machine needs.

:func:`multiband_10_15_10` is the three-band machine of the Atelier de
Tressage's circuit drawing (see the references page), sixteen gears::

    5  4  4  8  6  8  4  4  4  4  8  6  8  4  4  5
                ^                    ^
             split                 split

The two six-horn gears are split, cutting the line into bands of 24, 38 and
24 slots.  Each band holds at most half its slots, 12, 19 and 12 carriers, as
a flat braid does; the drawing runs 10, 15 and 10
(:data:`MULTIBAND_10_15_10_LOADING`).

:func:`twin_plait` is the smallest such machine: three gears, ``3 6 3``, and
two plaits braided side by side.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

from .model import BraidingMachine, Connection, HornGear

#: The smallest line that braids two bands: an end gear of three slots, a
#: six-slot gear split three and three, and another end gear.  Each band is
#: three slots of end gear and three of split gear, the smallest flat braid
#: there is: two plaits side by side.
TWIN_PLAIT_SLOTS = (3, 6, 3)

#: Its one split gear.
TWIN_PLAIT_SPLIT = (1,)

#: Slots per gear along the line, read off the circuit drawing.  The gears
#: lie on a line folded round into nearly a circle; its ends never join.
MULTIBAND_10_15_10_SLOTS = (5, 4, 4, 8, 6, 8, 4, 4, 4, 4, 8, 6, 8, 4, 4, 5)

#: The gears split between the bands on either side of them.
MULTIBAND_10_15_10_SPLIT = (4, 11)

#: Where the reference machine's carriers start, band by band: 10, 15 and 10,
#: the 10-15-10 of its name.  Not the most it holds: found by the exact
#: loading search, which gives 12, 19 and 12 at most, and
#: thinned to the drawing's counts as evenly over the gears as they go; the
#: tests run it over the whole machine's period, 2280 steps.
MULTIBAND_10_15_10_LOADING = (
    (
        ("G0", 0),
        ("G0", 2),
        ("G0", 4),
        ("G1", 2),
        ("G1", 3),
        ("G2", 1),
        ("G2", 2),
        ("G3", 2),
        ("G3", 4),
        ("G4a", 1),
    ),
    (
        ("G4b", 0),
        ("G4b", 2),
        ("G5", 2),
        ("G5", 4),
        ("G6", 1),
        ("G6", 2),
        ("G7", 2),
        ("G7", 3),
        ("G8", 1),
        ("G8", 2),
        ("G9", 2),
        ("G9", 3),
        ("G10", 1),
        ("G10", 3),
        ("G11a", 2),
    ),
    (
        ("G11b", 0),
        ("G11b", 1),
        ("G12", 1),
        ("G12", 3),
        ("G13", 2),
        ("G13", 3),
        ("G14", 1),
        ("G14", 2),
        ("G15", 2),
        ("G15", 4),
    ),
)


def bands_of(n_gears: int, split: Sequence[int]) -> tuple[tuple[int, int], ...]:
    """Which gears each band of a line runs over: from an end or a split gear
    to the next.

    Args:
        n_gears: Gears along the line.
        split: The split gears.

    Returns:
        Per band, its first and last gear; a split gear is the last of one
        band and the first of the next.
    """
    cuts = [0, *sorted(split), n_gears - 1]
    return tuple(itertools.pairwise(cuts))


def gear_name(index: int, split: Sequence[int], side: int = 0) -> str:
    """The name of gear ``index``, or of one half of it if it is split.

    Args:
        index: Position along the line.
        split: The split gears.
        side: For a split gear, -1 for the half serving the band before it,
            +1 for the band after it.

    Returns:
        ``G<index>``, with ``a`` or ``b`` for a half.
    """
    if index not in split:
        return f"G{index}"
    return f"G{index}{'a' if side < 0 else 'b'}"


class MultibandLine(BraidingMachine):
    """A line of gears cut into bands by split gears, or some of its bands.

    Gear names and slot numbering are the whole line's whichever bands are
    built, so a loading reads the same on a band as on the whole machine.

    Args:
        slots: Slots per gear along the whole line; a split gear's count is
            that of the whole gear, both halves.
        split: Which gears are split between two bands.
        first: The first gear built.
        last: The last gear built.
        loading: The carriers to start with, if known; else searched for.
    """

    #: How far the line turns, end to end, folded round on itself.
    TURN = math.radians(310.0)

    def __init__(
        self,
        slots: Sequence[int],
        split: Sequence[int],
        first: int = 0,
        last: int | None = None,
        loading: Sequence[tuple[str, int]] | None = None,
    ):
        self.slots = tuple(slots)
        self.split = tuple(split)
        last = len(self.slots) - 1 if last is None else last
        self.first, self.last = first, last
        self._loading = None if loading is None else tuple(loading)
        for k in self.split:
            if self.slots[k] % 2:
                raise ValueError(
                    f"Split gear G{k} has {self.slots[k]} slots, not even."
                )
        gears: list[HornGear] = []
        for i in range(first, last + 1):
            turn = +1 if i % 2 == 0 else -1
            if i in self.split:
                half = self.slots[i] // 2
                if i > first:
                    gears.append(
                        HornGear(gear_name(i, split, -1), half, turn, self.slots[i])
                    )
                if i < last:
                    gears.append(
                        HornGear(gear_name(i, split, +1), half, turn, self.slots[i])
                    )
            else:
                gears.append(HornGear(f"G{i}", self.slots[i], turn))
        # An interior gear's two contacts sit opposite each other along the
        # line; a split half, like an end gear, has only one.
        connections = []
        for i in range(first, last):
            a, b = gear_name(i, split, +1), gear_name(i + 1, split, -1)
            one_contact = i == 0 or i in self.split
            connections.append(
                Connection(
                    a,
                    b,
                    slot_a0=0 if one_contact else self.slots[i] // 2,
                    slot_b0=0,
                    name=f"{a}-{b}",
                )
            )
        super().__init__(gears, connections)

    @property
    def bands(self) -> tuple[tuple[int, int], ...]:
        """Which gears each band of the whole line runs over: see
        :func:`bands_of`."""
        return bands_of(len(self.slots), self.split)

    def band_of(self, gear: str) -> int | None:
        """Which band a gear, or a split gear's half, serves.

        Args:
            gear: Gear name, ``G<index>``, with ``a`` or ``b`` for a half.

        Returns:
            The band, counted from 0 along the whole line; None if the line
            has no such gear.
        """
        try:
            index = int(gear[1:].rstrip("ab"))
        except ValueError:
            return None
        for band, (first, last) in enumerate(self.bands):
            if first <= index <= last:
                if gear.endswith("a") and index == first:
                    continue
                if gear.endswith("b") and index == last:
                    continue
                return band
        return None

    def default_carriers(self) -> dict[int, tuple[str, int]]:
        """The loading given, or one found by the loading search.

        Returns:
            Carrier number -> (gear, slot).
        """
        if self._loading is not None:
            return dict(enumerate(self._loading))
        return super().default_carriers()

    def preferred_layout(
        self, scale: float = 1.0
    ) -> dict[str, tuple[float, float]] | None:
        """Gear centres along the folded line, consecutive rims touching, a
        split gear's two halves on one centre.

        The line runs straight through a split gear, its two contacts
        opposite each other, so that each half's three horns stand exactly
        between the other's: the six make a regular hexagon.  It folds by the
        same angle at every other interior gear, :attr:`TURN` in all, which
        brings its ends round near each other without touching.

        The whole line's fold, whichever bands are built, so a band sits
        where it does in the whole machine.

        Args:
            scale: Overall scale factor.

        Returns:
            Gear name -> (x, y).
        """
        from .layout import _gear_radius

        radii = [_gear_radius(n, scale) for n in self.slots]
        bends = [i for i in range(1, len(self.slots) - 1) if i not in self.split]
        turn = self.TURN / len(bends) if bends else 0.0
        centres = [(0.0, 0.0)]
        # Its ends at the bottom, as in the drawing.
        heading = math.pi - self.TURN / 2
        for i in range(len(self.slots) - 1):
            if i in bends:
                heading += turn
            step = radii[i] + radii[i + 1]
            x, y = centres[-1]
            centres.append((x + step * math.cos(heading), y + step * math.sin(heading)))
        # Centred on the middle of the gears, so the fold sits in the picture.
        cx = sum(x for x, _ in centres) / len(centres)
        cy = sum(y for _, y in centres) / len(centres)
        layout = {}
        for name in self.gears:
            x, y = centres[int(name[1:].rstrip("ab"))]
            layout[name] = (x - cx, y - cy)
        return layout


def twin_plait() -> MultibandLine:
    """Two plaits braided at once on one line of three gears.

    The smallest machine with a split gear, to see what one does: two
    three-slot end gears either side of a six-slot gear split between them.
    Each band is a plait of three carriers, turned back on its own half of
    the middle gear; the two plaits share that gear and never meet.

    Returns:
        MultibandLine: the line, loaded with three carriers in each band.
    """
    return MultibandLine(TWIN_PLAIT_SLOTS, TWIN_PLAIT_SPLIT)


def multiband_10_15_10() -> MultibandLine:
    """The three-band 10-15-10 machine, loaded as its drawing is.

    Sixteen gears, the two six-horn ones split between the bands on either
    side; see the module.

    Returns:
        MultibandLine: the whole line.
    """
    return MultibandLine(
        MULTIBAND_10_15_10_SLOTS,
        MULTIBAND_10_15_10_SPLIT,
        loading=[p for band in MULTIBAND_10_15_10_LOADING for p in band],
    )


def multiband_band(band: int) -> MultibandLine:
    """One band of :func:`multiband_10_15_10`, on its own.

    Its gears, with the half of each split gear that serves it, and its part
    of the reference loading.  It braids exactly as it does in the whole
    machine: the other halves never meet it.

    Args:
        band: 0, 1 or 2, along the line.

    Returns:
        MultibandLine: that band's gears.

    Raises:
        ValueError: If ``band`` is not 0, 1 or 2.
    """
    bands = bands_of(len(MULTIBAND_10_15_10_SLOTS), MULTIBAND_10_15_10_SPLIT)
    if band not in range(len(bands)):
        raise ValueError(f"The machine has bands 0, 1 and 2, not {band!r}.")
    first, last = bands[band]
    return MultibandLine(
        MULTIBAND_10_15_10_SLOTS,
        MULTIBAND_10_15_10_SPLIT,
        first,
        last,
        loading=MULTIBAND_10_15_10_LOADING[band],
    )
