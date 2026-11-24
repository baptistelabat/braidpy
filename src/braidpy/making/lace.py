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
come with any signs, anywhere.  So the ring has notches to spare, and
before each crossing its two strands are brought, through the empty
notches between and beside them, to two notches whose gear turns the way
of the crossing's sign, crossing nobody; only those two move, and only if
they must.  Where both are hemmed in, the strands beside are pushed along
towards the nearest empty notch.  The strands keep their order and keep off
the ring's seam, as the strands of a word do (:mod:`braidpy.ring_program`);
and they end in the notches they began in, since a punchcard is run round
and round.

Spare notches cost gears but save steps: with one, every strand between a
pair and the spare notch must move for each sign that does not suit; with
one beside each strand, only the pair does.  So the strands are tried both
packed together and spread round the ring, on as many gears as are given
or on each number from the fewest to ``MOST_GEARS_PER_STRAND`` a strand,
and the card of fewest steps is kept, of fewest gears if two tie.  A
word shortened first (:meth:`braidpy.braid.Braid.shortened`) has fewer
crossings to make, and so fewer moves: Braid Studio shortens it so.

A step of the card is two lines over the gears, as the machine reads it:
the gears to turn anticlockwise, then those to turn clockwise.  The swaps
of a ring program's row share no notch, so their gears never touch, and a
row is a step: each swap is made in the first step after the last that
used either of its notches, so that moves of strands apart are made at
once.

:func:`lace_braid` reads the braid back off the machine: the punchcard is
run (:func:`~braidpy.horn_gear.simulation.simulate`), after each step each
bobbin is found in its notch, and each gear that turned swapped the two —
the machine's own motion, with each crossing the sign of the gear's turn.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from braidpy.braid import Braid
from braidpy.ring_program import RingProgram, Swap, _packed

Position = tuple[str, int]

__all__ = [
    "MOST_GEARS_PER_STRAND",
    "LaceCard",
    "lace_braid",
    "lace_card",
    "punchcard_text",
    "ring_braid",
]

# The most gears a card is tried on, for each strand: a notch spare beside
# every strand, so that only a crossing's two strands ever move.
MOST_GEARS_PER_STRAND = 2
# The fewest gears a lace ring has: two pairs, each turning its own way.
FEWEST_GEARS = 4


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
    steps: tuple[tuple[tuple[bool, ...], tuple[bool, ...]], ...]
    bobbins: tuple[int | None, ...]
    program: RingProgram

    def machine(self):
        """The lace machine, its gears driven by this card.

        Returns:
            A :class:`~braidpy.horn_gear.jacquard.JacquardLaceMachine`.
        """
        from braidpy.horn_gear.jacquard import jacquard_lace_ring

        return jacquard_lace_ring(
            self.n_gears, list(self.steps), threaded=self.threaded()
        )

    def threaded(self) -> list[int]:
        """The notches threaded, strand after strand."""
        where = {k: place for place, k in enumerate(self.bobbins) if k is not None}
        return [where[k] for k in sorted(where)]

    def threading(self) -> dict[int, tuple[str, int]]:
        """Where each strand's bobbin goes, as the machine numbers its slots.

        Returns:
            Strand → (gear, slot) of its notch.
        """
        from braidpy.horn_gear.jacquard import notch_positions

        notches = notch_positions(self.machine())
        return {
            k: notches[place] for place, k in enumerate(self.bobbins) if k is not None
        }

    def notches(self) -> list[str]:
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
        """The card as it is punched: see :func:`punchcard_text`."""
        return punchcard_text(self.steps)

    def spec(self, cycles: int = 1) -> dict[str, Any]:
        """The card as Braid Studio makes your own lace machine
        (:func:`braidpy.web.build`): its gears, the card as typed and the
        bobbins in their notches.

        Args:
            cycles: Passes of the card.

        Returns:
            The description, as the page writes it in its address.
        """
        return {
            "source": "lace",
            "name": "custom",
            "n_gears": self.n_gears,
            "card": card_digits(self.steps),
            "carriers": " ".join(self.notches()),
            "cycles": cycles,
        }


def card_digits(steps: Sequence[tuple[Sequence[bool], Sequence[bool]]]) -> str:
    """A lace machine's card as it is typed into Braid Studio: a step a line,
    the gears turning anticlockwise, then those turning clockwise, a 0 or 1 a
    gear.

    Args:
        steps: Per step, whether each gear turns anticlockwise, then
            clockwise.

    Returns:
        The card.
    """
    return "\n".join(
        " ".join("".join("1" if on else "0" for on in line) for line in step)
        for step in steps
    )


def punchcard_text(steps: Sequence[tuple[Sequence[bool], Sequence[bool]]]) -> str:
    """A lace machine's card as it is punched and as the machine's animation
    draws it (:func:`~braidpy.horn_gear.visualization.animate`): a column
    per gear, ● punched and ○ not, two lines per step read downwards — the
    anticlockwise line ↺, then the clockwise line ↻, half a punch to its
    right, as it is driven half a step later.

    Args:
        steps: Per step, whether each gear turns anticlockwise, then
            clockwise.

    Returns:
        The card, the gears named along the top.
    """
    n_gears = len(steps[0][0])
    names = " ".join(chr(ord("A") + g) for g in range(n_gears))
    width = len(str(len(steps) - 1))
    lines = [f"{'':>{width}}    {names}"]

    def punched(line: Sequence[bool]) -> str:
        return " ".join("●" if on else "○" for on in line)

    for number, (ccw, cw) in enumerate(steps):
        lines.append(f"{number:>{width}} ↺  {punched(ccw)}")
        lines.append(f"{'':>{width}} ↻   {punched(cw)}")
    return "\n".join(lines)


def _gear_sign(gear: int) -> int:
    """The sign of the crossings a gear makes: + anticlockwise (even)."""
    return 1 if gear % 2 == 0 else -1


def lace_card(braid: Braid, n_gears: Optional[int] = None) -> LaceCard:
    """A braid as a lace machine's punchcard of as few steps as are found;
    see the module.

    Args:
        braid: The braid.
        n_gears: Gears round the ring: even, at least ``FEWEST_GEARS``, and
            more than the strands, a notch being spare.  If None, each
            number from the fewest that do to ``MOST_GEARS_PER_STRAND`` a
            strand is tried.

    Returns:
        The card.  :func:`lace_braid` reads back the same braid, exactly.

    Raises:
        ValueError: If ``n_gears`` cannot hold the strands with a notch to
            spare, or is odd or below ``FEWEST_GEARS``.
    """
    n = braid.n_strands
    fewest = max(FEWEST_GEARS, n + 1 + (n + 1) % 2)
    if n_gears is not None and (
        n_gears < FEWEST_GEARS or n_gears % 2 or n_gears < n + 1
    ):
        raise ValueError(
            f"A lace ring needs an even number of at least {FEWEST_GEARS} "
            f"gears, and a notch to spare: {n} strands cannot go on {n_gears}."
        )
    tried = (
        [n_gears]
        if n_gears is not None
        else list(range(fewest, max(fewest, MOST_GEARS_PER_STRAND * n) + 1, 2))
    )
    word = [int(g) for g in braid.generators]
    cards = [
        _card(word, n, gears, start)
        for gears in tried
        for start in {tuple(range(n)), tuple(k * gears // n for k in range(n))}
    ]
    return min(cards, key=lambda card: (len(card.steps), card.n_gears))


def _card(word: Sequence[int], n: int, gears: int, start: Sequence[int]) -> LaceCard:
    """A word's card on ``gears`` gears, its ``n`` strands starting in the
    notches ``start``, in order (:func:`lace_card`)."""
    moves = _Moves(gears, start)
    for g in word:
        moves.cross(abs(g) - 1, 1 if g > 0 else -1)
    moves.home()
    bobbins: list[int | None] = [None] * gears
    for k, notch in enumerate(start):
        bobbins[notch] = k
    # A braid of no crossing is a step turning no gear: a card has a step.
    rows = _packed(gears, moves.swaps) or ((),)
    program = RingProgram(gears, tuple(bobbins), rows)
    steps = []
    for row in program.rows:
        turning = {(swap.place + 1) % gears for swap in row}
        ccw = tuple(g in turning and g % 2 == 0 for g in range(gears))
        cw = tuple(g in turning and g % 2 == 1 for g in range(gears))
        steps.append((ccw, cw))
    return LaceCard(gears, tuple(steps), tuple(bobbins), program)


class _Moves:
    """The swaps that make a word on a lace ring, worked out crossing by
    crossing (:func:`lace_card`): the strands in notches ``start``, in
    order, kept so; each gear's turn a swap of the sign it turns."""

    def __init__(self, gears: int, start: Sequence[int]) -> None:
        self.gears = gears
        self.start = list(start)
        self.held: list[int | None] = [None] * gears
        for k, notch in enumerate(start):
            self.held[notch] = k
        self.notch = list(start)
        # The strand at each position of the word, from the left.
        self.order = list(range(len(start)))
        self.swaps: list[Swap] = []

    def _turn(self, place: int) -> None:
        """Gear ``place + 1`` turns, its notches swapping what they hold."""
        self.swaps.append(Swap(place, _gear_sign(place + 1)))
        held = self.held
        held[place], held[place + 1] = held[place + 1], held[place]
        for notch in (place, place + 1):
            strand = held[notch]
            if strand is not None:
                self.notch[strand] = notch

    def _walk(self, strand: int, to: int) -> None:
        """A strand moved notch by notch to ``to``, through empty ones."""
        while self.notch[strand] != to:
            here = self.notch[strand]
            self._turn(here if to > here else here - 1)

    def _room(self, notch: int, way: int) -> int | None:
        """The nearest empty notch from ``notch`` on, ``way`` (-1 or +1);
        None if the ring's end comes first."""
        while 0 <= notch < self.gears and self.held[notch] is not None:
            notch += way
        return notch if 0 <= notch < self.gears else None

    def _push(self, notch: int, way: int, room: int) -> None:
        """The strands from ``notch`` to the empty notch ``room``, ``way``
        (-1 or +1), each moved one notch along, so that ``notch`` is
        empty."""
        for place in range(room - way, notch - way, -way):
            strand = self.held[place]
            assert strand is not None
            self._walk(strand, place + way)

    def cross(self, position: int, sign: int) -> None:
        """The strands at ``position`` and the next, in the word's order,
        brought to a gear turning the way of ``sign``, and crossed."""
        left, right = self.order[position], self.order[position + 1]
        x, y = self.notch[left], self.notch[right]
        places = self._places(x, y, sign)
        if not places:
            # Hemmed in: the strands beside pushed away, the fewer the better.
            beside = {-1: x - 1, 1: y + 1}
            rooms = {
                way: room
                for way, notch in beside.items()
                if (room := self._room(notch, way)) is not None
            }
            way = min(rooms, key=lambda w: abs(rooms[w] - beside[w]))
            self._push(beside[way], way, rooms[way])
            places = self._places(x, y, sign)
        place = min(places, key=lambda p: abs(x - p) + abs(y - p - 1))
        # The one moving outwards first, into the room it leaves the other.
        if place < x:
            self._walk(left, place)
            self._walk(right, place + 1)
        else:
            self._walk(right, place + 1)
            self._walk(left, place)
        self.swaps.append(Swap(place, sign))
        held = self.held
        held[place], held[place + 1] = held[place + 1], held[place]
        self.notch[left], self.notch[right] = place + 1, place
        self.order[position], self.order[position + 1] = right, left

    def _places(self, x: int, y: int, sign: int) -> list[int]:
        """Where two neighbouring strands, in notches ``x`` and ``y``, can be
        crossed with ``sign``: the notches ``p`` and ``p + 1`` within the
        empty ones round them, gear ``p + 1`` turning the way of ``sign``."""
        low, high = x, y
        while low > 0 and self.held[low - 1] is None:
            low -= 1
        while high < self.gears - 1 and self.held[high + 1] is None:
            high += 1
        return [p for p in range(low, high) if _gear_sign(p + 1) == sign]

    def home(self) -> None:
        """Every strand back to a notch it began in, the leftmost strand to
        the leftmost: those moving left from the left, those moving right
        from the right, so none is in another's way."""
        for k, strand in enumerate(self.order):
            if self.start[k] < self.notch[strand]:
                self._walk(strand, self.start[k])
        for k in reversed(range(len(self.order))):
            strand = self.order[k]
            if self.start[k] > self.notch[strand]:
                self._walk(strand, self.start[k])


def card_program(
    n_gears: int,
    steps: Sequence[tuple[Sequence[bool], Sequence[bool]]],
    threaded: Optional[Sequence[int]] = None,
) -> RingProgram:
    """A punchcard run on its ring, as neighbours swapping places: what the
    machine does, worked out without building it.

    Gear ``g`` turning swaps the bobbins of notches ``g - 1`` and ``g``, the
    crossing the sign of its turn: + anticlockwise (an even gear), - clockwise
    (an odd one).  A step's anticlockwise line turns first, then its
    clockwise line, as the machine reads them: a row each.

    Args:
        n_gears: Gears round the ring.
        steps: Per step, whether each gear turns anticlockwise, then
            clockwise.
        threaded: The notch of each strand's bobbin, strand after strand;
            every notch if None.

    Returns:
        The ring program, notches being its places.

    Raises:
        ValueError: If a gear is asked to turn the way it does not.
    """
    if threaded is None:
        threaded = range(n_gears)
    start: list[int | None] = [None] * n_gears
    for k, notch in enumerate(threaded):
        start[notch] = k
    rows: list[tuple[Swap, ...]] = []
    for number, step in enumerate(steps):
        for line, parity in zip(step, (0, 1)):
            turning = [g for g, on in enumerate(line) if on]
            wrong = [g for g in turning if g % 2 != parity]
            if wrong:
                way = "anticlockwise" if parity == 0 else "clockwise"
                raise ValueError(
                    f"Step {number}: gears {wrong} cannot turn {way}; "
                    "A, C, E... turn anticlockwise, B, D, F... clockwise."
                )
            rows.append(tuple(Swap((g - 1) % n_gears, _gear_sign(g)) for g in turning))
    return RingProgram(n_gears, tuple(start), tuple(rows))


def lace_braid(card: LaceCard) -> Braid:
    """The braid a punchcard makes on the lace machine, read off the
    machine itself (:func:`ring_braid`), threaded as the card says.

    Args:
        card: The card, and its threading.

    Returns:
        The braid.
    """
    return ring_braid(card.machine(), card.threading())


def ring_braid(machine, threading: Optional[Mapping[int, Position]] = None) -> Braid:
    """The braid one pass of a lace machine's card makes, read off the
    machine itself: the card run, each bobbin found in its notch after each
    step, and the two bobbins of each gear that turned swapped — with the
    sign of that gear's turn, + anticlockwise.

    Args:
        machine: A lace ring
            (:func:`~braidpy.horn_gear.jacquard.jacquard_lace_ring`).
        threading: Each bobbin's place at the start, as (gear, slot); the
            machine's own threading if None.  Bobbins are the braid's
            strands, numbered in the order they are given.

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
        slot_angles,
    )
    from braidpy.horn_gear.simulation import simulate

    threading = dict(machine.default_carriers() if threading is None else threading)
    strand = {k: number for number, k in enumerate(threading)}
    names = list(machine.gears)
    gears = len(names)
    sign = [machine.gears[name].direction for name in names]
    layout = compute_layout(machine)
    angles = slot_angles(machine, layout)
    riding = {name: carrier_radius(machine, layout, name) for name in names}
    notch_xy = [
        carrier_xy(machine, layout, angles, riding, place, 0)
        for place in _notches(machine)
    ]
    # A step of the card is two of the machine's: one per line.
    history = simulate(machine, 2 * len(machine.program), threading)

    def held(state) -> list[int | None]:
        here: list[int | None] = [None] * gears
        for carrier in state.carriers:
            x, y = carrier_xy(
                machine, layout, angles, riding, carrier.position, state.time
            )
            notch = min(
                range(gears),
                key=lambda k: math.hypot(notch_xy[k][0] - x, notch_xy[k][1] - y),
            )
            here[notch] = strand[carrier.carrier_id]
        return here

    rows = []
    before = held(history[0])
    for number, step in enumerate(machine.program):
        # The two lines are driven one after the other: a gear of the second
        # may take a bobbin the first has just brought.  Bobbins are found
        # only after the whole step, where they sit exactly in their notches.
        expected = list(before)
        for line in step:
            turned = [g for g in range(gears) if line[g]]
            if not turned:
                continue
            rows.append(tuple(Swap((g - 1) % gears, sign[g]) for g in turned))
            for g in turned:
                left, right = (g - 1) % gears, g
                expected[left], expected[right] = expected[right], expected[left]
        after = held(history[2 * (number + 1)])
        if expected != after:
            raise RuntimeError(
                f"Step {number}: the bobbins are in {after}, not {expected}."
            )
        before = after
    return RingProgram(gears, tuple(held(history[0])), tuple(rows)).braid()


def _notches(machine) -> list[tuple[str, int]]:
    from braidpy.horn_gear.jacquard import notch_positions

    notches = notch_positions(machine)
    return [notches[k] for k in sorted(notches)]
