# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a punchcard for the Jacquard lace machine.

braidpy's lace machine (:func:`~braidpy.horn_gear.jacquard.jacquard_lace_ring`)
is a ring of 2-slot gears.  A bobbin sits in a **notch**, cut where two
neighbouring gears overlap — notch ``k`` between gears ``k`` and ``k + 1`` —
and a gear's half turn swaps the bobbins of its two notches: gear ``g``,
notches ``g - 1`` and ``g``.  The notches are a ring of places, and a half
turn a swap of neighbours (:class:`~braidpy.ring_program.RingProgram`).

A gear always turns the same way, and neighbours turn opposite ways, so
which bobbin passes over is fixed by where the crossing is made: a gear
turning anticlockwise (an even one) makes a positive crossing, one turning
clockwise a negative one.  A braid word does not care: its crossings may
come with any signs, anywhere.  So the strands are kept side by side with
a notch to spare, and when a crossing's sign is not its gear's, they all
move along one notch, into the spare one, crossing nobody: every gear
under them is then of the other way.  They only ever move between two
neighbouring positions, so they keep off the ring's seam, as the strands
of a word do (:mod:`braidpy.ring_program`); and they end where they began,
since a punchcard is run round and round.

A step of the card is two lines over the gears, as the machine reads it:
the gears to turn anticlockwise, then those to turn clockwise.  The swaps
of a ring program's row share no notch, so their gears never touch, and a
row is a step.

:func:`lace_braid` reads the braid back off the machine: the punchcard is
run (:func:`~braidpy.horn_gear.simulation.simulate`), after each step each
bobbin is found in its notch, and each gear that turned swapped the two —
the machine's own motion, with each crossing the sign of the gear's turn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from braidpy.braid import Braid
from braidpy.ring_program import RingProgram, Swap, _packed

__all__ = ["LaceCard", "lace_braid", "lace_card"]


@dataclass(frozen=True)
class LaceCard:
    """A punchcard for the lace machine, and how to thread it.

    Args:
        n_gears: Gears round the ring.
        steps: Per step, the two lines of the card: per gear, whether it
            turns anticlockwise, then whether it turns clockwise.
        bobbins: The strand in each notch to begin with, or None.
        program: The same as a ring program, places being notches.
    """

    n_gears: int
    steps: Tuple[Tuple[Tuple[bool, ...], Tuple[bool, ...]], ...]
    bobbins: Tuple[Optional[int], ...]
    program: RingProgram

    def machine(self):
        """The lace machine, its gears driven by this card.

        Returns:
            A :class:`~braidpy.horn_gear.jacquard.JacquardLaceMachine`.
        """
        from braidpy.horn_gear.jacquard import jacquard_lace_ring

        return jacquard_lace_ring(self.n_gears, list(self.steps))

    def threading(self) -> Dict[int, Tuple[str, int]]:
        """Where each strand's bobbin goes, as the machine numbers its slots.

        Returns:
            Strand → (gear, slot) of its notch.
        """
        from braidpy.horn_gear.jacquard import notch_positions

        notches = notch_positions(self.machine())
        return {
            k: notches[place] for place, k in enumerate(self.bobbins) if k is not None
        }

    def notches(self) -> List[str]:
        """The notches to put a bobbin in, named by the two gears that cut
        each — "A-B" — as the lace ring names its contacts; worked out
        without building the machine, which needs networkx.

        Returns:
            The notches threaded, strand after strand.
        """
        names = [chr(ord("A") + g) for g in range(self.n_gears)]
        where = {k: place for place, k in enumerate(self.bobbins) if k is not None}
        return [
            f"{names[where[k]]}-{names[(where[k] + 1) % self.n_gears]}"
            for k in sorted(where)
        ]

    def text(self) -> str:
        """The card as it is punched and as the machine's animation draws it
        (:func:`~braidpy.horn_gear.visualization.animate`): a column per
        gear, ● punched and ○ not, two lines per step read downwards — the
        anticlockwise line ↺, then the clockwise line ↻, half a punch to its
        right, as it is driven half a step later."""
        names = " ".join(chr(ord("A") + g) for g in range(self.n_gears))
        width = len(str(len(self.steps) - 1))
        lines = [f"{'':>{width}}    {names}"]

        def punched(line: Tuple[bool, ...]) -> str:
            return " ".join("●" if on else "○" for on in line)

        for number, (ccw, cw) in enumerate(self.steps):
            lines.append(f"{number:>{width}} ↺  {punched(ccw)}")
            lines.append(f"{'':>{width}} ↻   {punched(cw)}")
        return "\n".join(lines)


def _gear_sign(gear: int) -> int:
    """The sign of the crossings a gear makes: + anticlockwise (even)."""
    return 1 if gear % 2 == 0 else -1


def lace_card(braid: Braid, n_gears: Optional[int] = None) -> LaceCard:
    """A braid as a lace machine's punchcard; see the module.

    Args:
        braid: The braid.
        n_gears: Gears round the ring: even, at least 4, and more than the
            strands, a notch being spare.  The fewest that do if None.

    Returns:
        The card.  :func:`lace_braid` reads back the same braid, exactly.

    Raises:
        ValueError: If ``n_gears`` cannot hold the strands with a notch to
            spare, or is odd or below 4.
    """
    n = braid.n_strands
    gears = n_gears if n_gears is not None else max(4, n + 1 + (n + 1) % 2)
    if gears < 4 or gears % 2 or gears < n + 1:
        raise ValueError(
            f"A lace ring needs an even number of at least 4 gears, and a "
            f"notch to spare: {n} strands cannot go on {gears}."
        )
    offset = 0
    swaps: List[Swap] = []

    def shift(to: int) -> None:
        """Every strand one notch along, into the spare one: no crossing."""
        nonlocal offset
        if to > offset:
            # Rightwards: the front strand first, into the spare notch.
            places = range(offset + n - 1, offset - 1, -1)
        else:
            places = range(offset - 1, offset + n - 1)
        for place in places:
            swaps.append(Swap(place, _gear_sign(place + 1)))
        offset = to

    for g in braid.generators:
        i, sign = abs(int(g)), 1 if g > 0 else -1
        if _gear_sign(offset + i) != sign:
            shift(1 - offset)
        swaps.append(Swap(offset + i - 1, sign))
    # A card is run round and round: it ends with the strands back in the
    # notches they began in, so the next time round is the same braid.
    if offset:
        shift(0)

    start: List[Optional[int]] = [None] * gears
    for k in range(n):
        start[k] = k
    program = RingProgram(gears, tuple(start), _packed(gears, swaps))
    steps = []
    for row in program.rows:
        turning = {(swap.place + 1) % gears for swap in row}
        ccw = tuple(g in turning and g % 2 == 0 for g in range(gears))
        cw = tuple(g in turning and g % 2 == 1 for g in range(gears))
        steps.append((ccw, cw))
    return LaceCard(gears, tuple(steps), tuple(start), program)


def lace_braid(card: LaceCard) -> Braid:
    """The braid a punchcard makes on the lace machine, read off the
    machine itself: the card run, each bobbin found in its notch after each
    step, and the two bobbins of each gear that turned swapped — with the
    sign of that gear's turn.

    Args:
        card: The card, and its threading.

    Returns:
        The braid.

    Raises:
        RuntimeError: If a bobbin is found anywhere but where the card's
            gears should have taken it.
    """
    from braidpy.horn_gear.layout import (
        carrier_radius,
        carrier_xy,
        compute_layout,
        slot_offsets,
    )
    from braidpy.horn_gear.simulation import simulate

    machine = card.machine()
    gears = card.n_gears
    threading = card.threading()
    layout = compute_layout(machine)
    offsets = slot_offsets(machine, layout)
    riding = {name: carrier_radius(machine, layout, name) for name in machine.gears}
    notch_xy = [
        carrier_xy(machine, layout, offsets, riding, place, 0)
        for place in _notches(machine)
    ]
    # A step of the card is two of the machine's: one per line.
    history = simulate(machine, 2 * len(card.steps), threading)

    def held(state) -> List[Optional[int]]:
        here: List[Optional[int]] = [None] * gears
        for carrier in state.carriers:
            x, y = carrier_xy(
                machine, layout, offsets, riding, carrier.position, state.time
            )
            notch = min(
                range(gears),
                key=lambda k: math.hypot(notch_xy[k][0] - x, notch_xy[k][1] - y),
            )
            here[notch] = carrier.carrier_id
        return here

    rows = []
    before = held(history[0])
    for number, (ccw, cw) in enumerate(card.steps):
        after = held(history[2 * (number + 1)])
        turned = [g for g in range(gears) if ccw[g] or cw[g]]
        row = tuple(Swap((g - 1) % gears, _gear_sign(g)) for g in turned)
        expected = list(before)
        for g in turned:
            left, right = (g - 1) % gears, g
            expected[left], expected[right] = expected[right], expected[left]
        if expected != after:
            raise RuntimeError(
                f"Step {number}: the bobbins are in {after}, not {expected}."
            )
        rows.append(row)
        before = after
    return RingProgram(gears, tuple(held(history[0])), tuple(rows)).braid()


def _notches(machine) -> List[Tuple[str, int]]:
    from braidpy.horn_gear.jacquard import notch_positions

    notches = notch_positions(machine)
    return [notches[k] for k in sorted(notches)]
