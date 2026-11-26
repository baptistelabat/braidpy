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
one beside each strand, only the pair does.  Where the strands begin
matters as much: begun a notch along, the plait's crossings all fall on
gears of their signs.  So the strands are tried packed together from every
notch, spread a notch apart and spread evenly (:func:`_starts`), on as many
gears as are given or on each number from the fewest to
``MOST_GEARS_PER_STRAND`` a strand; then searched, a few hundred tries
seeded: the crossings in other orders where they commute
(:func:`_reordered`), the strands begun anywhere, a crossing at times at
the next nearest gear of its sign.  The card of fewest steps is kept, of
fewest gears if two tie.  A word shortened first
(:meth:`braidpy.braid.Braid.shortened`) has fewer crossings to make, and so
fewer moves: Braid Studio shortens it so.

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
import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from braidpy.braid import Braid
from braidpy.ring_program import RingProgram, Swap, _packed

Position = tuple[str, int]

__all__ = [
    "MOST_GEARS_PER_STRAND",
    "LaceCard",
    "card_conjugate",
    "card_names",
    "gear_name",
    "gear_number",
    "lace_braid",
    "lace_card",
    "punchcard_text",
    "read_card",
    "repeat_floor",
    "ring_braid",
    "step_floor",
]

# Letters to name gears with, A to Z (gear_name), and how a card by gear
# names writes a step that turns no gear (card_names).
LETTERS = 26
STILL = "-"
# The most gears a card is tried on, for each strand: a notch spare beside
# every strand, so that only a crossing's two strands ever move.
MOST_GEARS_PER_STRAND = 2
# The fewest gears a lace ring has: two pairs, each turning its own way.
FEWEST_GEARS = 4
# The search for a card of fewer steps (lace_card): how many tries at most,
# and at most so many crossings made in all, which a second or two takes in
# a browser; how often a try takes the crossings in another order, and how
# often a crossing goes to the next nearest gear of its sign; and the seed,
# so that a braid always has the same card.
SEARCH_RUNS = 300
SEARCH_CROSSINGS = 30000
# And before it, each way of beginning the strands on each number of gears,
# so many crossings made at most: every so many ways, if they are more.
TRIED_CROSSINGS = 100000
REORDERED = 0.7
NEXT_NEAREST = 0.2
SEED = 0
# The search tries the numbers of gears of the best cards found without it,
# so many of them, and begins the strands anywhere so often.
SEARCH_GEARS = 3
ANYWHERE = 0.3
# The search for a conjugate of fewer steps (card_conjugate): so many words
# tried, a hundredth of a second each on the book's sinnets; and the
# temperature it begins at, in steps, and how fast it cools, each try.
CONJUGATE_TRIES = 3000
# At most so many crossings counted in all, each try counting three times
# the word's: a second or two in a browser.
CONJUGATE_CROSSINGS = 300000
WARM = 1.0
COOLING = 0.999
COLD = 0.05


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
        where = {k: place for place, k in enumerate(self.bobbins) if k is not None}
        return [
            f"{gear_name(where[k])}-{gear_name((where[k] + 1) % self.n_gears)}"
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
            "card": card_names(self.steps),
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


def gear_name(gear: int) -> str:
    """A lace ring's gear by name, as its card and its notches name it: A
    to Z, then AA, AB… as a spreadsheet names its columns.

    Args:
        gear: The gear, from 0.

    Returns:
        Its name.
    """
    name = ""
    gear += 1
    while gear:
        gear, letter = divmod(gear - 1, LETTERS)
        name = chr(ord("A") + letter) + name
    return name


def gear_number(name: str) -> int:
    """The gear a name names (:func:`gear_name`), from 0, whatever its case.

    Args:
        name: The name.

    Returns:
        The gear.

    Raises:
        ValueError: If the name is not letters.
    """
    if not re.fullmatch(r"[A-Za-z]+", name):
        raise ValueError(f"{name!r} is not a gear: gears are named A, B… Z, AA, AB…")
    gear = 0
    for letter in name.upper():
        gear = gear * LETTERS + ord(letter) - ord("A") + 1
    return gear - 1


def card_names(steps: Sequence[tuple[Sequence[bool], Sequence[bool]]]) -> str:
    """A lace machine's card by the gears each step turns, as a link writes
    it and Braid Studio takes it: a step after another, ``/`` between, its
    gears by name, ``-`` for none.  A gear always turns its own way, so the
    names say which line of the step each is on: A, C, E… anticlockwise,
    first; B, D, F… clockwise, after.  Far shorter than its digits
    (:func:`card_digits`), mostly 0.

    Args:
        steps: Per step, whether each gear turns anticlockwise, then
            clockwise.

    Returns:
        The card.
    """
    return " / ".join(
        " ".join(gear_name(g) for g in range(len(ccw)) if ccw[g] or cw[g]) or STILL
        for ccw, cw in steps
    )


def read_card(
    text: str, n_gears: int
) -> list[tuple[tuple[bool, ...], tuple[bool, ...]]]:
    """A card as it is typed: by the gears each step turns
    (:func:`card_names`), or as digits (:func:`card_digits`), groups of 0
    and 1, a digit a gear, taken two by two — the gears turning
    anticlockwise, then clockwise — however the steps are laid out on lines.

    Args:
        text: The card.
        n_gears: Gears round the ring.

    Returns:
        Per step, whether each gear turns anticlockwise, then clockwise.

    Raises:
        ValueError: If a group is not of 0 and 1, a digit a gear, or the
            groups do not make whole steps; or a gear named is not on the
            ring.
    """
    groups = re.findall(r"\S+", text)
    if groups and not all(re.fullmatch(r"[01]+", group) for group in groups):
        return _read_names(text, n_gears)
    for group in groups:
        if len(group) != n_gears:
            raise ValueError(
                f"{group!r} has {len(group)} digits: give one for each of the "
                f"{n_gears} gears."
            )
    if not groups:
        raise ValueError(
            "Give the card: per step, the gears turning anticlockwise, then clockwise."
        )
    if len(groups) % 2:
        raise ValueError(
            "A step is two groups: the gears turning anticlockwise, then those "
            "turning clockwise."
        )
    return [
        (tuple(c == "1" for c in groups[k]), tuple(c == "1" for c in groups[k + 1]))
        for k in range(0, len(groups), 2)
    ]


def _read_names(
    text: str, n_gears: int
) -> list[tuple[tuple[bool, ...], tuple[bool, ...]]]:
    """A card by the gears each step turns (:func:`read_card`)."""
    steps = []
    for step in text.strip().strip("/").split("/"):
        turning = set()
        for name in step.split():
            if name == STILL:
                continue
            gear = gear_number(name)
            if gear >= n_gears:
                raise ValueError(f"No gear {name} on a ring of {n_gears} gears.")
            turning.add(gear)
        steps.append(
            (
                tuple(g in turning and g % 2 == 0 for g in range(n_gears)),
                tuple(g in turning and g % 2 == 1 for g in range(n_gears)),
            )
        )
    return steps


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
        The card, the gears named along the top (:func:`gear_name`), a
        column as wide as the longest name: AA and on, past 26 gears.
    """
    n_gears = len(steps[0][0])
    names = [gear_name(g) for g in range(n_gears)]
    column = max(map(len, names))
    width = len(str(len(steps) - 1))
    # The clockwise line half a column to the right.
    half = " " * ((column + 1) // 2)

    def row(marks: Sequence[str]) -> str:
        return " ".join(mark.ljust(column) for mark in marks).rstrip()

    def punched(line: Sequence[bool]) -> str:
        return row(["●" if on else "○" for on in line])

    lines = [f"{'':>{width}}    {row(names)}"]
    for number, (ccw, cw) in enumerate(steps):
        lines.append(f"{number:>{width}} ↺  {punched(ccw)}")
        lines.append(f"{'':>{width}} ↻  {half}{punched(cw)}")
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
    # Each number of gears and each way of placing the strands, the moves
    # as they come: (steps, gears, start, swaps).
    starts = {gears: _starts(n, gears) for gears in tried}
    # As many as the budget allows, every so many of each gear count's.
    allowed = max(len(tried), TRIED_CROSSINGS // max(1, len(word)))
    every = -(-sum(map(len, starts.values())) // allowed)
    found = [
        _tried(word, gears, start)
        for gears in tried
        for start in starts[gears][::every]
    ]
    found.sort(key=lambda tried_: tried_[:2])
    best = found[0]
    # Then the search, on the gears of the best cards so far: the crossings
    # in other orders, where they commute; the strands begun anywhere; and
    # a crossing sometimes at another gear than the nearest.  Seeded, so a
    # braid always has the same card.
    gears_tried = list(dict.fromkeys(tried_[1] for tried_ in found))[:SEARCH_GEARS]
    rng = random.Random(SEED)
    runs = _tries(SEARCH_RUNS, SEARCH_CROSSINGS, len(word))
    for run in range(runs):
        gears = gears_tried[run % len(gears_tried)]
        order = _reordered(word, rng) if rng.random() < REORDERED else word
        start = (
            tuple(sorted(rng.sample(range(gears), n)))
            if rng.random() < ANYWHERE
            else rng.choice(_starts(n, gears))
        )
        best = min(best, _tried(order, gears, start, rng), key=lambda t: t[:2])
    _, gears, start, swaps = best
    return _card(gears, start, swaps)


def _tries(most: int, crossings: int, per_try: int) -> int:
    """How many tries a search makes: at most ``most``, and no more than
    ``crossings`` made or counted in all, ``per_try`` in each."""
    return min(most, crossings // max(1, per_try))


def _starts(n: int, gears: int) -> list[tuple[int, ...]]:
    """Where the strands may begin, in order: packed together from each
    notch; a notch spare beside each, from the first notch or the second;
    and spread evenly over the ring, or over part of it, from either end.  Which suits a braid's signs best
    depends on where its crossings fall on gears of either way: shifted a
    notch, the plait's are every one its gear's."""
    starts = [tuple(range(offset, offset + n)) for offset in range(gears - n + 1)]
    starts += [
        tuple(offset + 2 * k for k in range(n))
        for offset in (0, 1)
        if offset + 2 * (n - 1) < gears
    ]
    # Spread evenly over every width the ring holds, from either end: a
    # ring of more gears than a braid needs holds what a smaller one does.
    starts += [
        tuple(offset + k * width // n for k in range(n))
        for width in range(n, gears + 1)
        for offset in {0, gears - width}
    ]
    return sorted(set(starts))


def _reordered(word: Sequence[int], rng: random.Random) -> list[int]:
    """The word's crossings in a random order that keeps the braid: a
    crossing only moved past crossings of strands apart from its own,
    which commute with it."""
    later: list[list[int]] = [[] for _ in word]
    waiting = [0] * len(word)
    last: dict[int, int] = {}
    for k, g in enumerate(word):
        for place in {abs(g) - 1, abs(g), abs(g) + 1} & last.keys():
            later[last[place]].append(k)
            waiting[k] += 1
        last[abs(g)] = k
    ready = [k for k in range(len(word)) if not waiting[k]]
    order = []
    while ready:
        k = ready.pop(rng.randrange(len(ready)))
        order.append(word[k])
        for after in later[k]:
            waiting[after] -= 1
            if not waiting[after]:
                ready.append(after)
    return order


def _tried(
    word: Sequence[int],
    gears: int,
    start: tuple[int, ...],
    rng: Optional[random.Random] = None,
) -> tuple[int, int, tuple[int, ...], list[Swap]]:
    """A word's moves on ``gears`` gears from ``start``, and how many steps
    they take once packed: the nearest gear for each crossing, or with
    ``rng`` sometimes the next nearest."""
    moves = _Moves(gears, start, rng)
    for g in word:
        moves.cross(abs(g) - 1, 1 if g > 0 else -1)
    moves.home()
    return len(_packed(gears, moves.swaps)), gears, start, moves.swaps


def _card(gears: int, start: Sequence[int], swaps: Sequence[Swap]) -> LaceCard:
    """The card of these moves on ``gears`` gears, the strands beginning in
    the notches ``start``, in order (:func:`lace_card`)."""
    bobbins: list[int | None] = [None] * gears
    for k, notch in enumerate(start):
        bobbins[notch] = k
    # A braid of no crossing is a step turning no gear: a card has a step.
    rows = _packed(gears, swaps) or ((),)
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
    order, kept so; each gear's turn a swap of the sign it turns.  With
    ``rng``, a crossing is sometimes made at the next nearest gear of its
    sign, ``NEXT_NEAREST`` of the time, and a tie broken at random."""

    def __init__(
        self, gears: int, start: Sequence[int], rng: Optional[random.Random] = None
    ) -> None:
        self.gears = gears
        self.rng = rng
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
            way = min(
                rooms,
                key=lambda w: (
                    abs(rooms[w] - beside[w]),
                    self.rng and self.rng.random(),
                ),
            )
            self._push(beside[way], way, rooms[way])
            places = self._places(x, y, sign)
        places.sort(key=lambda p: abs(x - p) + abs(y - p - 1))
        nearer = (
            self.rng is None or len(places) < 2 or self.rng.random() >= NEXT_NEAREST
        )
        place = places[0] if nearer else places[1]
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


def _finishes(word: Sequence[int], n_strands: int) -> list[int]:
    """The earliest step each crossing of a word can be made at on a lace
    ring (:func:`step_floor`)."""
    order = list(range(n_strands))
    last: list[int | None] = [None] * n_strands
    went = [0] * n_strands
    finish = [0] * len(word)
    for k, g in enumerate(word):
        i = abs(g) - 1
        earliest = 0
        for strand, way in ((order[i], 1), (order[i + 1], -1)):
            j = last[strand]
            if j is not None:
                # The same way again, with the same sign: a notch to move.
                again = went[strand] == way and (word[j] > 0) == (g > 0)
                earliest = max(earliest, finish[j] + again)
        finish[k] = earliest + 1
        for strand, way in ((order[i], 1), (order[i + 1], -1)):
            last[strand], went[strand] = k, way
        order[i], order[i + 1] = order[i + 1], order[i]
    return finish


def step_floor(word: Sequence[int], n_strands: int) -> int:
    """The fewest steps any card for a word can take, on any lace ring: no
    fewer than its longest chain of crossings each waiting for the last,
    a crossing waiting a step more when a strand of it crossed last the
    same way with the same sign.  Neighbouring gears turn opposite ways,
    so its two gears are of the same way, a notch apart: it must move a
    notch between.  On the small braids of the catalogue, the fewest steps
    there are, found by trying every turn of every gear, are this or a
    few more.

    Args:
        word: The crossings, ``i`` for ``σᵢ`` and ``-i`` for ``σᵢ⁻¹``.
        n_strands: The strands.

    Returns:
        The floor, in steps.
    """
    return max(_finishes(word, n_strands), default=0)


def repeat_floor(word: Sequence[int], n_strands: int) -> int:
    """The fewest steps a repeat of a word can take on a card run round and
    round (:func:`step_floor`), once the repeats follow one another: what
    a third repeat adds to two.  It does not depend on where the word is
    cut: every rotation of a word has the same.

    Args:
        word: The crossings of one repeat.
        n_strands: The strands.

    Returns:
        The floor, in steps a repeat.
    """
    word = list(word)
    finish = _finishes(word * 3, n_strands)
    return max(finish, default=0) - max(finish[: 2 * len(word)], default=0)


def card_conjugate(
    braid: Braid, tries: int = CONJUGATE_TRIES, seed: int = SEED
) -> Braid:
    """A conjugate of a braid whose repeats a lace card makes in fewer
    steps: the same braid, once repeated, seen another way.

    The word is read round, as a card runs it, and rewritten by the braid
    relations (:mod:`braidpy.shortening`), wherever the word is cut:
    crossings of strands apart swapped, three crossings of three strands
    made the other way round.  Reading it from elsewhere conjugates it, and
    a relation keeps it, so each word met is a conjugate.  A rewrite that
    lowers the floor a repeat (:func:`repeat_floor`) is kept, one that
    raises it now and then, less and less often, so as to cross what does
    not change it.  Seeded, so a braid always has the same conjugate.  The
    book's sinnets, written as cascades of one strand crossing many, come
    out with a floor a third of theirs or less.

    Args:
        braid: The braid.
        tries: How many rewrites are tried, at most: fewer for a long word
            (``CONJUGATE_CROSSINGS``).
        seed: The search's seed.

    Returns:
        The conjugate of lowest floor found: the braid if none is lower.
    """
    from braidpy.shortening import rewrites

    n = braid.n_strands
    current = tuple(int(g) for g in braid.generators)
    floor = repeat_floor(current, n)
    best = (floor, current)
    rng = random.Random(seed)
    warmth = WARM
    # Each try counts three repeats of the word (repeat_floor).
    budget = _tries(tries, CONJUGATE_CROSSINGS, 3 * len(current))
    for _ in range(budget if len(current) > 2 else 0):
        cut = rng.randrange(len(current))
        found = list(rewrites(current[cut:] + current[:cut]))
        if not found:
            continue
        candidate = rng.choice(found)
        lower = repeat_floor(candidate, n)
        if lower <= floor or rng.random() < math.exp((floor - lower) / warmth):
            current, floor = candidate, lower
            if floor < best[0]:
                best = (floor, current)
        warmth = max(COLD, warmth * COOLING)
    return Braid(best[1], n)


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
