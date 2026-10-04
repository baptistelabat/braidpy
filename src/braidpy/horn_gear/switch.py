# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/switch.py
===================

Switches: contacts that hand over only some of the slots presented to them.

An ordinary contact takes whatever arrives.  A carrier riding an interior gear
therefore leaves by the contact it did not come in through, which is why a
line of gears braids one band however long it is: every carrier ends up
walking the whole line.

A **switch** is a contact that only lets some of a gear's slots cross.  Put one
on each side of a gear and its slots divide into two groups that never mix: a
carrier arriving in a slot of the far group is simply not taken when it reaches
the far contact, so it stays on the gear, comes round again -- spiralling, as a
braider would say -- and goes back out the way it came.

That is what lets one line of gears braid several bands at once.  The gear
carrying a switch on each side belongs to the bands on both sides of it, and
hands each of them back its own carriers.  It is the mechanism of the
three-band machines, where two such gears cut a line of sixteen into bands of
ten, fifteen and ten.

The switch is keyed on the slot's own index, not on the step, which is what
makes it hold: a carrier may only cross while an allowed slot is presented, so
it can only ever come back into the group it left from.
"""

import math
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from braidpy.horn_gear.model import Axial, BraidingMachine, Connection, HornGear


class SwitchError(ValueError):
    """A switch that does not name a real connection, gear or slot."""


@dataclass(frozen=True)
class Switch:
    """A contact that only hands over the slots it is set to.

    Args:
        connection: Name of the :class:`~braidpy.horn_gear.model.Connection`
            the switch sits on.
        gear: Which of that connection's two gears the slots are counted on.
        slots: Slot indices of ``gear`` allowed to cross.  Any other slot
            arriving at this contact stays on its gear and rides round.
    """

    connection: str
    gear: str
    slots: FrozenSet[int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "slots", frozenset(self.slots))


class SwitchedMachine(BraidingMachine):
    """A braiding machine with switches on some of its contacts.

    Everything else behaves as on an ordinary machine: the gears are tangent,
    each slot belongs to one gear, and a carrier rides its slot round until it
    reaches a contact.  The only difference is that a switched contact may
    decline to take it, in which case it stays where it is and comes round
    again.

    Args:
        gears: The gears.
        connections: The contacts between them.
        switches: The switched contacts.
        axials: Cores that never ride a horn.

    Raises:
        SwitchError: If a switch names a connection, gear or slot that does
            not exist.
    """

    def __init__(
        self,
        gears: List[HornGear],
        connections: List[Connection],
        switches: Iterable[Switch] = (),
        axials: Iterable[Axial] = (),
    ):
        super().__init__(gears, connections, axials=axials)
        self.switches: Tuple[Switch, ...] = tuple(switches)

        by_name = {c.name: c for c in self.connections if c.name}
        self._allowed: Dict[Tuple[str, str], FrozenSet[int]] = {}
        for sw in self.switches:
            conn = by_name.get(sw.connection)
            if conn is None:
                raise SwitchError(
                    f"switch names connection {sw.connection!r}, which this "
                    f"machine does not have"
                )
            if sw.gear not in (conn.gear_a, conn.gear_b):
                raise SwitchError(
                    f"switch on {sw.connection!r} counts slots on {sw.gear!r}, "
                    f"which is not one of its gears"
                )
            n_slots = self.gears[sw.gear].n_slots
            bad = [s for s in sw.slots if not 0 <= s < n_slots]
            if bad:
                raise SwitchError(
                    f"switch on {sw.connection!r} allows slots {sorted(bad)} of "
                    f"{sw.gear!r}, which has only {n_slots}"
                )
            key = (sw.connection, sw.gear)
            self._allowed[key] = self._allowed.get(key, frozenset()) | sw.slots

    def _crossing_allowed(self, gear_name: str, slot: int, time: int) -> bool:
        """Whether the contact this slot has reached will take it."""
        for conn in self.connections_of(gear_name):
            if not conn.name:
                continue
            slot_a, slot_b = conn.slots_at(self, time)
            mine = slot_a if conn.gear_a == gear_name else slot_b
            if mine != slot:
                continue
            # A switch set on either side governs the crossing, so that the
            # two groups of slots stay apart whichever way a carrier is going.
            if not self.contact_exchanges(conn, time):
                return False
        return True

    def contact_exchanges(self, conn: Connection, time: int) -> bool:
        """Whether this contact hands anything over at ``time``.

        A switched contact that will not take the slots presented to it is not
        exchanging, and its deflector holds the two gears' paths apart, so
        carriers may ride past on either side of it at once.

        Args:
            conn: The contact in question.
            time: Step being taken.

        Returns:
            True if the contact is exchanging this step.
        """
        if not conn.name:
            return True
        slot_a, slot_b = conn.slots_at(self, time)
        for side, presented in ((conn.gear_a, slot_a), (conn.gear_b, slot_b)):
            allowed = self._allowed.get((conn.name, side))
            if allowed is not None and presented not in allowed:
                return False
        return True

    def next_position(self, pos: Tuple[str, int], time: int) -> Tuple[str, int]:
        """Where a carrier goes, with a switched contact free to decline it.

        Args:
            pos: Current (gear_name, slot_index).
            time: Step being taken.

        Returns:
            The (gear_name, slot_index) the carrier occupies afterwards.  A
            carrier a switch declines keeps its slot and rides on.
        """
        gear_name, slot = pos
        if gear_name not in self.turning_gears(time):
            return pos
        neighbor = self.neighbor_at_slot(gear_name, slot, time + 1)
        if neighbor is None:
            return pos
        if not self._crossing_allowed(gear_name, slot, time + 1):
            return pos
        return neighbor


#: Slots per gear along the line of a three-band 10-15-10 machine.
#:
#: Read off the circuit drawing of a "3 bandes 10-15-10" published by the
#: Atelier de Tressage; see the references page.  The gears lie on a *line*,
#: folded round into nearly a circle to save floor space, so the two ends
#: nearly meet but never join.  The sequence is a palindrome, with the 5-slot
#: gears at the two ends and the two 6-slot gears where the bands divide.
MULTIBAND_10_15_10_SLOTS = (5, 4, 4, 8, 6, 8, 4, 4, 4, 4, 8, 6, 8, 4, 4, 5)

#: Which gears of that line each band runs over, as (first, last) indices.
#: The 6-slot gears at 4 and 11 belong to the two bands on either side of them.
MULTIBAND_10_15_10_BANDS = ((0, 4), (4, 11), (11, 15))

#: Carriers each band of the reference machine runs -- the 10-15-10 of its name.
MULTIBAND_10_15_10_CARRIERS = (10, 15, 10)


class MultibandLine(SwitchedMachine):
    """A line of gears folded round until its ends nearly meet.

    The gears lie on a line and are wired as one, but a line of sixteen is
    long and a braiding shop is not, so the real machine curves it round into
    nearly a circle.  :func:`~braidpy.horn_gear.layout.compute_layout` would
    draw the line straight, which is correct and unreadable, so the fold is
    pinned here.

    The ends stop short of each other by design: joining them would close the
    ring and make a quite different machine.
    """

    #: How much of a full turn the folded line spans, leaving the ends apart.
    SPAN = math.radians(330.0)

    def preferred_layout(
        self, scale: float = 1.0
    ) -> Optional[Dict[str, Tuple[float, float]]]:
        """Gear centres along an arc, consecutive rims touching as on the line.

        Args:
            scale: Overall scale factor.

        Returns:
            Gear name → (x, y).
        """
        names = [f"G{i}" for i in range(len(MULTIBAND_10_15_10_SLOTS))]
        radii = [math.sqrt(n) * scale for n in MULTIBAND_10_15_10_SLOTS]
        chords = [radii[i] + radii[i + 1] for i in range(len(radii) - 1)]

        def span(radius: float) -> float:
            # Each chord subtends 2*asin(d/2R); they must add up to SPAN.
            return sum(2 * math.asin(min(1.0, d / (2 * radius))) for d in chords)

        lo, hi = max(chords) / 2 + 1e-9, sum(chords)
        for _ in range(200):
            mid = (lo + hi) / 2
            if span(mid) > self.SPAN:
                lo = mid
            else:
                hi = mid
        radius = (lo + hi) / 2

        layout, angle = {}, -self.SPAN / 2
        for i, name in enumerate(names):
            layout[name] = (radius * math.cos(angle), radius * math.sin(angle))
            if i < len(chords):
                angle += 2 * math.asin(min(1.0, chords[i] / (2 * radius)))
        return layout


def multiband_10_15_10() -> SwitchedMachine:
    """A line of sixteen gears braiding three bands at once.

    Sixteen gears, 86 slots, slot counts
    ``5 4 4 8 6 8 4 4 4 4 8 6 8 4 4 5`` -- a line, not a ring, folded round
    until its ends nearly touch.  Without switches it would braid a single
    band: every interior gear has two contacts, so a carrier entering by one
    leaves by the other and walks the whole line, which is one closed circuit
    over all 86 slots.

    The two 6-slot gears carry a switch on each side, dividing their slots
    between the band to their left and the band to their right.  A carrier
    reaching the far contact in a slot that contact will not take stays on the
    gear, comes round again and goes back the way it came.  Those two gears
    therefore belong to both of the bands they separate, handing each one back
    its own carriers, and the line braids three bands of ten, fifteen and ten.

    Each band runs two circuits, one each way, which is what the drawing shows
    by giving every band two colours.

    Returns:
        MultibandLine: the three-band line, with its fold pinned.
    """
    slots = MULTIBAND_10_15_10_SLOTS
    gears = [
        HornGear(f"G{i}", n, direction=+1 if i % 2 == 0 else -1)
        for i, n in enumerate(slots)
    ]
    connections = [
        Connection(
            f"G{i}",
            f"G{i + 1}",
            slot_a0=0 if i == 0 else slots[i] // 2,
            slot_b0=0,
            name=f"G{i}-G{i + 1}",
        )
        for i in range(len(slots) - 1)
    ]
    # Alternate slots serve alternate bands.  Giving each band a contiguous
    # half of the gear separates them just as well but costs much more of the
    # machine's capacity, because carriers then queue at the switched contact.
    switches: List[Switch] = []
    for gear in (4, 11):
        inward = frozenset(range(0, slots[gear], 2))
        outward = frozenset(range(1, slots[gear], 2))
        switches.append(Switch(f"G{gear - 1}-G{gear}", f"G{gear}", inward))
        switches.append(Switch(f"G{gear}-G{gear + 1}", f"G{gear}", outward))
    return MultibandLine(gears, connections, switches)


def band_of(gear: str) -> Optional[int]:
    """Which band of :func:`multiband_10_15_10` a gear belongs to.

    The two shared gears belong to two bands at once, so this gives the first
    of them; :data:`MULTIBAND_10_15_10_BANDS` has the full picture.

    Args:
        gear: Gear name, ``G0`` to ``G15``.

    Returns:
        The band index from 0, or None if the gear is not on this machine.
    """
    try:
        index = int(gear[1:])
    except (ValueError, IndexError):
        return None
    for band, (first, last) in enumerate(MULTIBAND_10_15_10_BANDS):
        if first <= index <= last:
            return band
    return None
