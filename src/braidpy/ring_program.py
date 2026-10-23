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

Conventions.  The ring is seen from above, from the side the braider
works from on a kumihimo disk, and the braid is made downwards, away from
the eye, as it hangs below a disk.  Places are numbered 0 to ``n - 1``
clockwise, the seam between the last and place 0.  A swap of place ``p``
exchanges what places ``p`` and ``p + 1`` hold:

- two strands make a crossing.  At a positive swap, ``+1``, the strand at
  ``p + 1`` goes first, anticlockwise, lifted over the one at ``p`` — over
  as seen from above, so passing inside it, nearer the braid's axis — and
  the strand at ``p`` then moves clockwise into the place it left.  At a
  negative swap, ``-1``, the strand at ``p`` goes first, clockwise, over the
  one at ``p + 1``.  With the strands at places 1 to ``n``, counted from
  the seam, the positive swap of place ``i - 1`` is ``σᵢ``, the negative
  one ``σᵢ⁻¹``: the disk's own reading
  (:func:`~braidpy.take_off.disk_annular_word`) reads them back so;
- a strand and an empty place make no crossing: the strand moves on by one
  place, to the empty one, and the swap's sign changes nothing;
- two empty places: nothing moves.

The ring has a seam, between its last place and its first.  Strands carried
across it twist the braid below them, as carriers going round a tubular
braiding machine do: every strand once round the ring is a full twist.
That is still a braid, and often a shorter way to make one; but a braid
word has its strands in a row from the seam, so the ways made from a word
keep them off it for now, and make that very word.  Shorter programs, going
over the seam, are for later.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

from braidpy.braid import Braid

__all__ = ["RingProgram", "Swap", "from_braid", "same_braid"]


@dataclass(frozen=True)
class Swap:
    """Two neighbouring places exchanging what they hold: a crossing if both
    hold a strand, a strand moved on by one place if one is empty.  See the
    module for which way round.

    Args:
        place: The place ``p``, 0-based; it swaps with place ``p + 1``,
            clockwise from it seen from above, the last place with place 0.
        sign: The crossing's sign, if two strands cross: +1 when the strand
            at ``p + 1`` is lifted over the one at ``p``, -1 when the one at
            ``p`` is lifted over the one at ``p + 1``.  It changes nothing
            when a place is empty.
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
    start: tuple[int | None, ...]
    rows: tuple[tuple[Swap, ...], ...]

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

    def swaps(self) -> list[Swap]:
        """Every swap, row after row."""
        return [swap for row in self.rows for swap in row]

    def disk(self) -> tuple[dict[Hashable, int], list[dict[Hashable, int]]]:
        """The program as a disk's moves: each strand's slot, 1-based, and
        per step, the one strand that moves and by how much — as
        :func:`~braidpy.take_off.disk_annular_word` and Braid Studio take
        them.  A swap is the lifted strand moved over its neighbour, then the
        neighbour moved into the place it left.

        Returns:
            The start and the steps.
        """
        start: dict[Hashable, int] = {
            k: place + 1 for place, k in enumerate(self.start) if k is not None
        }
        held = dict(enumerate(self.start))
        steps: list[dict[Hashable, int]] = []
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

    def ends(self) -> tuple[int | None, ...]:
        """The strand at each place once the program is done."""
        held = list(self.start)
        for swap in self.swaps():
            right = (swap.place + 1) % self.n_places
            held[swap.place], held[right] = held[right], held[swap.place]
        return tuple(held)


def _packed(n_places: int, swaps: Sequence[Swap]) -> tuple[tuple[Swap, ...], ...]:
    """Swaps in rows: each in the first row after the last that used either
    of its places.  Swaps of no place in common commute, so the braid is
    unchanged."""
    free_from = [0] * n_places
    rows: list[list[Swap]] = []
    for swap in swaps:
        right = (swap.place + 1) % n_places
        row = max(free_from[swap.place], free_from[right])
        while len(rows) <= row:
            rows.append([])
        rows[row].append(swap)
        free_from[swap.place] = free_from[right] = row + 1
    return tuple(tuple(row) for row in rows)


def from_braid(
    braid: Braid, n_places: int | None = None, offset: int = 0
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
    start: list[int | None] = [None] * places
    for k in range(n):
        start[offset + k] = k
    swaps = [
        Swap(offset + abs(int(g)) - 1, 1 if g > 0 else -1) for g in braid.generators
    ]
    return RingProgram(places, tuple(start), _packed(places, swaps))


def same_braid(a: Braid, b: Braid) -> bool:
    """Whether two braids are the same braid, as the ways
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
