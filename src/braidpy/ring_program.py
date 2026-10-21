# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as neighbours swapping places round a ring: the step between a
braid and the ways of making it.

A braid word, a kumihimo disk, a lace machine: each makes a braid by
moving strands round a ring of places, two neighbours at a time.  A
:class:`RingProgram` says so once, for all of them: the places, which
strand starts where — a place may be empty — and rows of swaps, each two
neighbouring places exchanging what they hold, the swaps of a row sharing
no place so that they are made at once.  A braid becomes a ring program
(:func:`from_braid`), and a ring program becomes each way of making it;
read back as a braid (:meth:`RingProgram.braid`), each must be the braid
it was made from, as braidpy compares braids: by their topology
(:func:`same_braid`).

A swap's sign is the sign of the crossing it makes, as a braid word has
it: positive when the strand on the right, read round the ring, is lifted
over the one on its left — the convention of the disk's own reading
(:func:`~braidpy.take_off.disk_annular_word`), which reads it back.  A swap
with an empty place moves a strand on by one place and crosses nothing.

Moving strands round the ring is not free.  The ring has a seam, between
its last place and its first, and strands carried across it — every strand
once round the ring — twist the braid below them, as carriers going round
a tubular braiding machine do: once round is a full twist.  A program that
moves strands to other places through empty ones, to make a crossing
where a machine can, keeps them off the seam or brings them back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Hashable, List, Optional, Sequence, Tuple

from braidpy.braid import Braid

__all__ = ["RingProgram", "Swap", "from_braid", "same_braid"]


@dataclass(frozen=True)
class Swap:
    """Two neighbouring places exchanging what they hold.

    Args:
        place: The place on the left, 0-based; it swaps with the next one
            round the ring, the last place with the first.
        sign: The sign of the crossing made, +1 when the strand on the
            right is lifted over the one on the left, -1 the other way.
    """

    place: int
    sign: int


@dataclass(frozen=True)
class RingProgram:
    """A braid as neighbours swapping places round a ring; see the module.

    Args:
        n_places: Places round the ring.
        start: The strand at each place to begin with, 0 to ``n - 1``, or
            None where a place is empty.
        rows: The swaps, row after row; the swaps of a row share no place.

    Raises:
        ValueError: If a strand is missing or placed twice, a swap is off the
            ring or has no sign, or two swaps of a row share a place.
    """

    n_places: int
    start: Tuple[Optional[int], ...]
    rows: Tuple[Tuple[Swap, ...], ...]

    def __post_init__(self) -> None:
        if len(self.start) != self.n_places:
            raise ValueError(
                f"{len(self.start)} places given a strand or none, "
                f"for a ring of {self.n_places}."
            )
        strands = sorted(k for k in self.start if k is not None)
        if strands != list(range(len(strands))):
            raise ValueError(f"Strands 0 to n - 1, each once: got {strands}.")
        for number, row in enumerate(self.rows):
            used: set = set()
            for swap in row:
                if not 0 <= swap.place < self.n_places:
                    raise ValueError(f"Row {number}: no place {swap.place}.")
                if swap.sign not in (1, -1):
                    raise ValueError(f"Row {number}: a swap's sign is +1 or -1.")
                pair = {swap.place, (swap.place + 1) % self.n_places}
                if used & pair:
                    raise ValueError(f"Row {number}: two swaps share a place.")
                used |= pair

    @property
    def n_strands(self) -> int:
        """How many strands the ring holds."""
        return sum(k is not None for k in self.start)

    def swaps(self) -> List[Swap]:
        """Every swap, row after row."""
        return [swap for row in self.rows for swap in row]

    def disk(self) -> Tuple[Dict[Hashable, int], List[Dict[Hashable, int]]]:
        """The program as a disk's moves: each strand's slot, 1-based, and
        per step, the one strand that moves and by how much — as
        :func:`~braidpy.take_off.disk_annular_word` and Braid Studio take
        them.  A swap is the lifted strand moved over its neighbour, then the
        neighbour moved into the place it left.

        Returns:
            The start and the steps.
        """
        start: Dict[Hashable, int] = {
            k: place + 1 for place, k in enumerate(self.start) if k is not None
        }
        held = dict(enumerate(self.start))
        steps: List[Dict[Hashable, int]] = []
        for swap in self.swaps():
            left, right = swap.place, (swap.place + 1) % self.n_places
            a, b = held[left], held[right]
            # The strand lifted moves first, over the other.
            moves = [(b, -1), (a, +1)] if swap.sign > 0 else [(a, +1), (b, -1)]
            steps.extend({k: delta} for k, delta in moves if k is not None)
            held[left], held[right] = b, a
        return start, steps

    def braid(self) -> Braid:
        """The braid the program makes, as a braid word: read off its disk
        moves, as a disk braid is.

        Returns:
            The braid, on the program's strands.
        """
        from braidpy.annulus_braid import solid_word
        from braidpy.take_off import disk_annular_word

        start, steps = self.disk()
        annular, n = disk_annular_word(start, steps, self.n_places, clockwise=True)
        return Braid(tuple(solid_word(annular, n)), n)

    def ends(self) -> Tuple[Optional[int], ...]:
        """The strand at each place once the program is done."""
        held = list(self.start)
        for swap in self.swaps():
            right = (swap.place + 1) % self.n_places
            held[swap.place], held[right] = held[right], held[swap.place]
        return tuple(held)


def _packed(n_places: int, swaps: Sequence[Swap]) -> Tuple[Tuple[Swap, ...], ...]:
    """Swaps in rows: each in the first row after the last that used either
    of its places.  Swaps of no place in common commute, so the braid is
    unchanged."""
    free_from = [0] * n_places
    rows: List[List[Swap]] = []
    for swap in swaps:
        right = (swap.place + 1) % n_places
        row = max(free_from[swap.place], free_from[right])
        while len(rows) <= row:
            rows.append([])
        rows[row].append(swap)
        free_from[swap.place] = free_from[right] = row + 1
    return tuple(tuple(row) for row in rows)


def from_braid(
    braid: Braid, n_places: Optional[int] = None, offset: int = 0
) -> RingProgram:
    """A braid as a ring program: its strands side by side from place
    ``offset``, each crossing ``σᵢ^±1`` the strands at places
    ``offset + i - 1`` and ``offset + i`` swapping, packed into rows.

    Args:
        braid: The braid.
        n_places: Places round the ring; as many as strands if None.
        offset: The place of the first strand.  The strands stay clear of
            the seam, so ``offset + n_strands`` is at most ``n_places``.

    Returns:
        The program; :meth:`RingProgram.braid` is the braid exactly, its
        crossings in another order only where they commute.

    Raises:
        ValueError: If the strands do not fit between the seam and itself.
    """
    n = braid.n_strands
    places = n if n_places is None else n_places
    if offset < 0 or offset + n > places:
        raise ValueError(
            f"{n} strands from place {offset} do not fit a ring of {places} "
            "without crossing its seam."
        )
    start: List[Optional[int]] = [None] * places
    for k in range(n):
        start[offset + k] = k
    swaps = [
        Swap(offset + abs(int(g)) - 1, 1 if g > 0 else -1) for g in braid.generators
    ]
    return RingProgram(places, tuple(start), _packed(places, swaps))


def same_braid(a: Braid, b: Braid) -> bool:
    """Whether two braids are the same braid, as the bridges between ways
    of making one compare them: by their topology
    (:func:`~braidpy.similarity.same_fingerprint`), whatever their words.

    Args:
        a: A braid.
        b: Another.

    Returns:
        True if nothing measured tells them apart.
    """
    from braidpy.similarity import fingerprint, same_fingerprint

    return same_fingerprint(fingerprint(a), fingerprint(b))
