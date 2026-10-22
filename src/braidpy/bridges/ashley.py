# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching.

On Ashley's stand (:mod:`braidpy.ashley_solid_sinnet`) the strands lie in
spaces round the rim, and a move carries a strand from one space to
another, over every strand it passes.  A move is not a swap of neighbours,
so a braid cannot be turned into moves crossing by crossing as for a disk
or a lace machine: the bridge searches for a sinnet that makes it instead.

The sinnets searched are made as the book's are: every space gives a strand
and receives one in each cycle, so a cycle's moves follow a derangement of
the spaces — no space to itself — and every space has its strands back
after a cycle.  Each candidate is the strands shared out among the spaces,
the derangement, and the order of its moves.  A cycle read from another
move is the same braid, so the first move is taken from space 1.

A sinnet is found when its braid is the braid wanted, as the bridges
compare braids: by their topology
(:func:`~braidpy.ring_program.same_braid`) — the braid repeated, read from
any strand, however written.  Fewer spaces are tried first, so the simplest
sinnet is found first; the search stops at a time limit, and says whether
it tried everything it could.  Not every braid is a sinnet: when none is
found, the nearest is given, and how far it is
(:func:`~braidpy.similarity.distance`).

Every braid can be made on the stand, though, once its moves need not be a
sinnet's (:func:`ashley_moves`): one strand per space, with an empty space
after each, and each crossing made in three or four moves through the
empty spaces, every space holding what it held before.  It is the braid
itself, exactly, but no longer a sinnet of the book's kind: spaces give and
take strands unevenly, and a space can sit empty.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence, Tuple

from braidpy.ashley_solid_sinnet import AshleySolidSinnet
from braidpy.braid import Braid

__all__ = ["AshleySearch", "ashley_moves", "ashley_sinnet", "sinnet_spec"]


@dataclass(frozen=True)
class AshleySearch:
    """What a search for a sinnet found.

    Args:
        sinnet: A sinnet making the braid; None if none was found.
        nearest: The sinnet whose braid was nearest, found or not.
        distance: How far its braid is from the one wanted: 0 if found.
        tried: How many sinnets were tried.
        complete: Whether every sinnet of up to the spaces allowed was
            tried, rather than the time running out.
    """

    sinnet: Optional[AshleySolidSinnet]
    nearest: Optional[AshleySolidSinnet]
    distance: float
    tried: int
    complete: bool


def _compositions(total: int, parts: int) -> Iterator[Tuple[int, ...]]:
    """Every way of sharing ``total`` strands among ``parts`` spaces, each
    holding at least one."""
    for cuts in itertools.combinations(range(1, total), parts - 1):
        bounds = (0,) + cuts + (total,)
        yield tuple(b - a for a, b in zip(bounds, bounds[1:]))


def _derangements(n: int) -> Iterator[Tuple[int, ...]]:
    """Every permutation of ``range(n)`` moving every element."""
    for permutation in itertools.permutations(range(n)):
        if all(i != p for i, p in enumerate(permutation)):
            yield permutation


def _cycles(spaces: int) -> Iterator[List[Tuple[int, int]]]:
    """Every cycle of moves, each space moved from once and to once, its
    first move from space 1; spaces numbered from 1, as the book does."""
    for target in _derangements(spaces):
        for rest in itertools.permutations(range(1, spaces)):
            yield [(s + 1, target[s] + 1) for s in (0,) + rest]


def ashley_sinnet(
    braid: Braid,
    max_spaces: int = 6,
    time_limit: float = 20.0,
    spaces: Optional[Sequence[int]] = None,
) -> AshleySearch:
    """A sinnet on Ashley's stand that makes a braid; see the module.

    Args:
        braid: The braid wanted.
        max_spaces: The most spaces round the rim to try.
        time_limit: Seconds to search for, at most.
        spaces: The numbers of spaces to try, in order; 2 to
            ``max_spaces`` if None.

    Returns:
        The search: the sinnet found, or the nearest.
    """
    from braidpy.similarity import distance, fingerprint, same_fingerprint

    wanted = fingerprint(braid)
    n = braid.n_strands
    started = time.monotonic()
    tried = 0
    nearest: Optional[AshleySolidSinnet] = None
    nearest_distance = float("inf")
    counts_of = range(2, min(max_spaces, n) + 1) if spaces is None else spaces
    for count in counts_of:
        for counts in _compositions(n, count):
            for moves in _cycles(count):
                if time.monotonic() - started > time_limit:
                    return AshleySearch(None, nearest, nearest_distance, tried, False)
                sinnet = AshleySolidSinnet(list(counts), moves)
                tried += 1
                try:
                    made = sinnet.braid(1)
                except ValueError:
                    continue
                if not made.generators:
                    continue
                mark = fingerprint(made)
                if same_fingerprint(mark, wanted):
                    return AshleySearch(sinnet, sinnet, 0.0, tried, True)
                apart = distance(mark, wanted)
                if apart < nearest_distance:
                    nearest, nearest_distance = sinnet, apart
    return AshleySearch(None, nearest, nearest_distance, tried, True)


def ashley_moves(braid: Braid) -> AshleySolidSinnet:
    """Any braid on Ashley's stand, crossing by crossing; see the module.

    The strands lie one per odd space, from space 1, each followed by an
    empty even space: ``2n`` spaces for ``n`` strands.  A strand moved from
    an odd space goes anticlockwise, from an even one clockwise, over every
    strand it passes.  The two strands of ``σᵢ`` are in spaces ``a = 2(n -
    i) - 1`` and ``b = a + 2``, as the stand reads its strands the other way
    round, and the crossing is made through the empty spaces after them:

    - ``σᵢ``: ``b`` to ``b + 1``, ``b + 1`` to ``a + 1``, over the strand in
      ``a``; then ``a`` to ``b`` and ``a + 1`` back to ``a``;
    - ``σᵢ⁻¹``: ``a`` to ``b``, over the strand there; then ``b`` (its
      earlier strand) to ``b + 1``, and on to ``a``.

    Args:
        braid: The braid.

    Returns:
        The strands and moves, as a sinnet whose one cycle is the braid,
        exactly.
    """
    n = braid.n_strands
    moves: List[Tuple[int, int]] = []
    for g in braid.generators:
        a = 2 * (n - abs(int(g))) - 1
        b = a + 2
        if g > 0:
            moves += [(b, b + 1), (b + 1, a + 1), (a, b), (a + 1, a)]
        elif g < 0:
            moves += [(a, b), (b, b + 1), (b + 1, a)]
    return AshleySolidSinnet([1, 0] * n, moves)


def sinnet_spec(sinnet: AshleySolidSinnet, cycles: int = 4):
    """A sinnet as Braid Studio makes your own (:func:`braidpy.web.build`).

    Args:
        sinnet: The sinnet.
        cycles: How many cycles to make.

    Returns:
        The description.
    """
    return {
        "source": "sinnet",
        "name": "custom",
        "counts": " ".join(str(c) for c in sinnet.initial_counts_per_space),
        "moves": ", ".join(f"{a}>{b}" for a, b in sinnet.moves),
        "cycles": cycles,
    }
