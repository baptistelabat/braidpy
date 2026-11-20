# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching.

On Ashley's stand (:mod:`braidpy.ashley_solid_sinnet`) the strands lie in
spaces round the rim, and a move carries a strand from one space to
another, over every strand it passes.  A move is not a swap of neighbours,
so a braid cannot be turned into moves crossing by crossing as for a disk
or a lace machine: a sinnet that makes it is searched for instead.

The sinnets searched are made as the book's are: every space gives a strand
and receives one in each cycle, so a cycle's moves follow a derangement of
the spaces — no space to itself — and every space has its strands back
after a cycle.  Each candidate is the strands shared out among the spaces,
the derangement, and the order of its moves.  A cycle read from another
move is the same braid, so the first move is taken from space 1.

A sinnet is found when its braid is the braid wanted, compared as every
way of making a braid compares them: by their topology
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

A sinnet can also be made from the shape it is to take, as the book draws it
(:func:`sinnet_from_shape`): straight lines across the shape, parallel to
its sides, each turning at the outline in a bight into the next.  The
bights are the spaces, the lines the moves, made in the book's order.
And the other way: a sinnet's moves, grouped by the direction of their
lines (:func:`move_groups`), are the same at any size for shapes drawn on
one principle, and make its shape (:func:`shapes_from_moves`).
"""

from __future__ import annotations

import itertools
import math
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

import numpy as np

from braidpy.ashley_solid_sinnet import AshleySolidSinnet
from braidpy.braid import Braid

__all__ = [
    "AshleySearch",
    "FoundShape",
    "MoveGroups",
    "ShapeLine",
    "ashley_moves",
    "ashley_sinnet",
    "cell_outline",
    "corner_spaces",
    "grid_outline",
    "grid_shape",
    "least_counts",
    "move_groups",
    "oblong",
    "regular_polygon",
    "shape_diagram",
    "shape_lines",
    "shape_tracks",
    "shapes_from_moves",
    "sinnet_from_shape",
    "sinnet_spec",
    "triangle",
]


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

    sinnet: AshleySolidSinnet | None
    nearest: AshleySolidSinnet | None
    distance: float
    tried: int
    complete: bool


def _compositions(total: int, parts: int) -> Iterator[tuple[int, ...]]:
    """Every way of sharing ``total`` strands among ``parts`` spaces, each
    holding at least one."""
    for cuts in itertools.combinations(range(1, total), parts - 1):
        bounds = (0,) + cuts + (total,)
        yield tuple(b - a for a, b in itertools.pairwise(bounds))


def _derangements(n: int) -> Iterator[tuple[int, ...]]:
    """Every permutation of ``range(n)`` moving every element."""
    for permutation in itertools.permutations(range(n)):
        if all(i != p for i, p in enumerate(permutation)):
            yield permutation


def _cycles(spaces: int) -> Iterator[list[tuple[int, int]]]:
    """Every cycle of moves, each space moved from once and to once, its
    first move from space 1; spaces numbered from 1, as the book does."""
    for target in _derangements(spaces):
        for rest in itertools.permutations(range(1, spaces)):
            yield [(s + 1, target[s] + 1) for s in (0,) + rest]


def ashley_sinnet(
    braid: Braid,
    max_spaces: int = 6,
    time_limit_s: float = 20.0,
    spaces: Optional[Sequence[int]] = None,
) -> AshleySearch:
    """A sinnet on Ashley's stand that makes a braid; see the module.

    Args:
        braid: The braid wanted.
        max_spaces: The most spaces round the rim to try.
        time_limit_s: Seconds to search for, at most.
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
    nearest: AshleySolidSinnet | None = None
    nearest_distance = float("inf")
    counts_of = range(2, min(max_spaces, n) + 1) if spaces is None else spaces
    for count in counts_of:
        for counts in _compositions(n, count):
            for moves in _cycles(count):
                if time.monotonic() - started > time_limit_s:
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
    moves: list[tuple[int, int]] = []
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


# ----------------------------------------------------------- from a shape

# Ashley's diagrams, measured in spacings between neighbouring lines: a line
# runs parallel to a side of the shape, the first half a spacing in from it.
FIRST_LINE = 0.5
# Two points this close, in spacings, are one: where two lines meet the
# outline at one bight, or a bight is as near the first corner as another.
SAME_POINT = 1e-6


@dataclass(frozen=True)
class ShapeLine:
    """A line of Ashley's diagram, across the shape.

    Args:
        ends: Where it meets the outline, its two ends.
        direction: Which way it runs: the index of the first side of the
            outline parallel to it.
    """

    ends: tuple[tuple[float, float], tuple[float, float]]
    direction: int


def shape_lines(outline: Sequence[tuple[float, float]]) -> list[ShapeLine]:
    """The lines Ashley draws across a shape: parallel to each side, the
    first ``FIRST_LINE`` in from it, the others a spacing on, as many as fit
    strictly inside.  Parallel sides share their lines.  Where the outline
    turns back, as round the arms of an L or a U, a line is cut in pieces,
    each a line of its own.

    Args:
        outline: The shape's corners, anticlockwise, in spacings: any
            outline that does not cross itself.

    Returns:
        The lines, by direction, then from the side inwards.
    """
    corners = np.asarray(outline, dtype=float)
    sides = list(zip(corners, np.roll(corners, -1, axis=0)))
    lines: dict[tuple[int, float, float], ShapeLine] = {}
    for a, b in sides:
        along = (b - a) / np.linalg.norm(b - a)
        inward = np.array([-along[1], along[0]])
        direction = next(
            j
            for j, (c, d) in enumerate(sides)
            if abs(abs(np.dot((d - c) / np.linalg.norm(d - c), along)) - 1) < SAME_POINT
        )
        width = float(np.max((corners - a) @ inward))
        reference, end = sides[direction]
        across = np.array([-(end - reference)[1], (end - reference)[0]])
        across /= np.linalg.norm(across)
        distance = FIRST_LINE
        while distance < width - SAME_POINT:
            for ends in _pieces(sides, a + inward * distance, along):
                # Measured from the first side of this direction, so that a
                # line drawn from the side opposite is the same line; and,
                # of the pieces of one line, by where along it each is.
                middle = (ends[0] + ends[1]) / 2 - reference
                key = (
                    direction,
                    abs(round(float(np.dot(middle, across)), 6)),
                    round(float(np.dot(middle, end - reference)), 3),
                )
                lines.setdefault(
                    key, ShapeLine((_point(ends[0]), _point(ends[1])), direction)
                )
            distance += 1
    return [lines[key] for key in sorted(lines)]


def _point(xy) -> tuple[float, float]:
    """A point as two floats."""
    return float(xy[0]), float(xy[1])


def _pieces(sides, point, along) -> list[tuple[np.ndarray, np.ndarray]]:
    """The pieces of the line through ``point`` along ``along`` inside the
    outline, each by its two ends, in order along it: one across a convex
    shape, more where the outline turns back, as across the arms of a U."""
    normal = np.array([-along[1], along[0]])
    hits = []
    for c, d in sides:
        # Each side the line crosses, a corner on it counted once: with the
        # side it starts, not the one it ends.
        above_c = float(np.dot(c - point, normal)) > 0
        above_d = float(np.dot(d - point, normal)) > 0
        if above_c == above_d:
            continue
        matrix = np.array([along, c - d]).T
        t, _ = np.linalg.solve(matrix, c - point)
        hits.append(float(t))
    hits.sort()
    return [
        (point + hits[k] * along, point + hits[k + 1] * along)
        for k in range(0, len(hits) - 1, 2)
        if hits[k + 1] - hits[k] > SAME_POINT
    ]


def _round_the_outline(outline, point) -> tuple[float, int]:
    """How far round the outline a point on it is, anticlockwise from its
    first corner, and on which side."""
    corners = np.asarray(outline, dtype=float)
    travelled = 0.0
    for index, (a, b) in enumerate(zip(corners, np.roll(corners, -1, axis=0))):
        side = b - a
        length = float(np.linalg.norm(side))
        t = float(np.dot(point - a, side)) / length**2
        off = abs(side[0] * (point - a)[1] - side[1] * (point - a)[0]) / length
        if -SAME_POINT <= t <= 1 + SAME_POINT and off < SAME_POINT:
            return travelled + t * length, index
        travelled += length
    raise ValueError(f"{tuple(point)} is not on the outline.")


def _spaces(
    outline, lines: list[ShapeLine]
) -> tuple[list[tuple[float, float]], list[tuple[int, int]]]:
    """The bights, numbered as the book numbers the spaces: where each is, in
    their order, and the two each line joins.

    Two lines meeting the outline at one point turn into each other there:
    a bight.  The ends left over pair with their neighbours on the same side
    where they can, round a corner where they cannot.  The bights are
    numbered anticlockwise from the one nearest the first corner; of two as
    near, from the one before it.
    """
    corners = np.asarray(outline, dtype=float)
    perimeter = float(
        sum(
            np.linalg.norm(b - a) for a, b in zip(corners, np.roll(corners, -1, axis=0))
        )
    )
    ends = sorted(
        (*_round_the_outline(outline, np.asarray(end)), line, which)
        for line, shape_line in enumerate(lines)
        for which, end in enumerate(shape_line.ends)
    )
    pairs, lone = [], []
    k = 0
    while k < len(ends):
        if k + 1 < len(ends) and ends[k + 1][0] - ends[k][0] < SAME_POINT:
            pairs.append((ends[k], ends[k + 1]))
            k += 2
        else:
            lone.append(ends[k])
            k += 1
    if lone:
        # Two neighbours on one side make a bight if their lines are
        # parallel, as in a loop, or would meet beyond the outline, the
        # bight rounding off the point; not if they cross inside.  A bight
        # round a corner takes the two ends left there.  Of the two ways to
        # pair neighbours that do, the one turning fewer corners.
        options = [
            [
                (
                    lone[(2 * j + phase) % len(lone)],
                    lone[(2 * j + 1 + phase) % len(lone)],
                )
                for j in range(len(lone) // 2)
            ]
            for phase in (0, 1)
        ]
        options = [
            option
            for option in options
            if all(
                _turn_into(outline, lines[a[2]], lines[b[2]])
                for a, b in option
                if a[1] == b[1]
            )
        ] or options
        pairs += min(options, key=lambda option: sum(a[1] != b[1] for a, b in option))

    def place(pair) -> float:
        # The middle of a bight's two ends, the short way round.
        a, b = sorted((pair[0][0], pair[1][0]))
        if b - a > perimeter / 2:
            a += perimeter
        return ((a + b) / 2) % perimeter

    placed = sorted(pairs, key=place)
    first = min(
        range(len(placed)),
        key=lambda i: (
            round(min(place(placed[i]), perimeter - place(placed[i])), 6),
            place(placed[i]) < perimeter / 2,
        ),
    )
    placed = placed[first:] + placed[:first]
    space: dict[tuple[int, int], int] = {}
    for number, (a, b) in enumerate(placed, start=1):
        space[(a[2], a[3])] = space[(b[2], b[3])] = number
    where = [
        _point(
            (np.asarray(lines[a[2]].ends[a[3]]) + np.asarray(lines[b[2]].ends[b[3]]))
            / 2
        )
        for a, b in placed
    ]
    return where, [(space[(i, 0)], space[(i, 1)]) for i in range(len(lines))]


def shape_diagram(
    outline: Sequence[tuple[float, float]],
) -> tuple[list[ShapeLine], list[tuple[int, int]], list[tuple[float, float]]]:
    """Ashley's diagram of a shape: its lines (:func:`shape_lines`), the two
    spaces each joins, and where each bight is, space 1 first
    (:func:`sinnet_from_shape`).

    Args:
        outline: The shape's corners, anticlockwise, in spacings.

    Returns:
        The lines, the spaces each joins, and the bights.
    """
    lines = shape_lines(outline)
    bights, joins = _spaces(outline, lines)
    return lines, joins, bights


def _turn_into(outline, first: ShapeLine, second: ShapeLine) -> bool:
    """Whether two lines can turn into each other at the outline: they are
    parallel, or would meet beyond the outline, or on it."""
    p, q = (np.asarray(end) for end in first.ends)
    r, t = (np.asarray(end) for end in second.ends)
    matrix = np.array([q - p, r - t]).T
    if abs(np.linalg.det(matrix)) < SAME_POINT:
        return True
    along, _ = np.linalg.solve(matrix, r - p)
    meeting = p + along * (q - p)
    return not _inside(outline, meeting)


def _inside(outline, point) -> bool:
    """Whether a point is strictly inside the outline, not on it: the sides
    a ray from it crosses are odd in number."""
    corners = np.asarray(outline, dtype=float)
    inside = False
    for a, b in zip(corners, np.roll(corners, -1, axis=0)):
        side = b - a
        if abs(
            side[0] * (point - a)[1] - side[1] * (point - a)[0]
        ) < SAME_POINT * float(np.linalg.norm(side)) and -SAME_POINT <= float(
            np.dot(point - a, side)
        ) <= float(np.dot(side, side)):
            return False
        if (a[1] > point[1]) != (b[1] > point[1]):
            x = a[0] + (point[1] - a[1]) * side[0] / side[1]
            inside ^= x > point[0]
    return inside


def _in_order(
    n, joins, directions, first_side_direction, order: str = "book"
) -> list[tuple[int, int]]:
    """The lines as moves, in the book's order (:func:`sinnet_from_shape`):
    alternating, or space by space where that cannot be followed, or if
    ``order`` asks for it."""
    if order not in ORDERS:
        raise ValueError(f"No order {order!r}: one of {ORDERS}.")
    if order == "spaces":
        return _space_by_space(n, joins, directions, first_side_direction)
    try:
        moves = _alternating(n, joins, directions, first_side_direction)
    except ValueError:
        return _space_by_space(n, joins, directions, first_side_direction)
    every = list(range(1, n + 1))
    if sorted(a for a, _ in moves) != every or sorted(b for _, b in moves) != every:
        return _space_by_space(n, joins, directions, first_side_direction)
    return moves


# The orders the moves can be made in: the book's, alternating where it can,
# or space by space, 1, 2, 3 and on.
ORDERS = ("book", "spaces")


def _first_line(at, joins, directions, first_side_direction) -> int:
    """Space 1's line: the one across the first side, if one starts there."""
    return min(at[1], key=lambda line: directions[line] == first_side_direction)


def _lines_at(joins) -> dict[int, list[int]]:
    """Each space's two lines."""
    at: dict[int, list[int]] = {}
    for line, (a, b) in enumerate(joins):
        at.setdefault(a, []).append(line)
        at.setdefault(b, []).append(line)
    return at


def _space_by_space(n, joins, directions, first_side_direction):
    """The lines as moves, space 1 first, then 2, 3 and so on, each giving
    its strand: the book's order where the alternating one cannot be
    followed, as round a triangle of three lines a side (#3059).  Each
    curve of lines runs one way, the first space on it giving its strand
    along the way space 1's does, if it can."""
    at = _lines_at(joins)
    first = _first_line(at, joins, directions, first_side_direction)
    direction = directions[first]
    gives: dict[int, int] = {}
    for space in range(1, n + 1):
        if space in gives or any(
            gives.get(_other(joins[i], space)) == i for i in at[space]
        ):
            continue
        # The first space of a curve not yet run: run the curve from it.
        line = (
            first
            if space == 1
            else min(at[space], key=lambda i: directions[i] != direction)
        )
        here = space
        while here not in gives:
            gives[here] = line
            here = _other(joins[line], here)
            line = (
                next(i for i in at[here] if i != line)
                if len(set(at[here])) > 1
                else line
            )
    return [(space, _other(joins[gives[space]], space)) for space in range(1, n + 1)]


def _alternating(n, joins, directions, first_side_direction) -> list[tuple[int, int]]:
    """The lines as moves, each from the space beside where the last ended
    (:func:`sinnet_from_shape`)."""
    left = set(range(len(joins)))
    at = _lines_at(joins)
    # From space 1, along the line across the first side, if there is one.
    first = _first_line(at, joins, directions, first_side_direction)
    moves = [(1, _other(joins[first], 1))]
    left.discard(first)
    gave = {1}
    direction, step = directions[first], -1
    while left:
        start = (moves[-1][1] - 1 + step) % n + 1
        here = sorted(line for line in at[start] if line in left)
        if not here:
            raise ValueError(
                f"Space {start} has no line left: not one of Ashley's shapes."
            )
        line = ([i for i in here if directions[i] == direction] or here)[0]
        if start in gave:
            # The space has given its strand: take the line coming to it.
            moves.append((_other(joins[line], start), start))
        else:
            moves.append((start, _other(joins[line], start)))
        left.discard(line)
        gave.add(moves[-1][0])
        direction, step = directions[line], -step
    return moves


def _other(join: tuple[int, int], space: int) -> int:
    """The space at a line's other end."""
    return join[1] if join[0] == space else join[0]


def least_counts(moves: Sequence[tuple[int, int]], n_spaces: int) -> list[int]:
    """The fewest strands each space can start with so that none is ever left
    empty: two in a space that gives its strand before it is given one in
    the cycle, one in any other.

    Args:
        moves: The moves of a cycle, every space giving and receiving once.
        n_spaces: How many spaces.

    Returns:
        The strands of each space, space 1 first.
    """
    gives = {a: k for k, (a, _) in enumerate(moves)}
    receives = {b: k for k, (_, b) in enumerate(moves)}
    return [2 if gives[s] < receives[s] else 1 for s in range(1, n_spaces + 1)]


def corner_spaces(outline: Sequence[tuple[float, float]]) -> list[int]:
    """The spaces at a shape's corners, where the book adds strands to
    sharpen its edges: each bight turning a corner, its two lines ending on
    two sides, and each bight alone on its side, as at the ends of a flat
    oblong.  Spaces 1, 5 and 9 of a triangle of four lines a side (#3049),
    1 and 7 of an oblong of 10 by 2 (#3072).

    Args:
        outline: The shape's corners, anticlockwise, in spacings.

    Returns:
        The spaces, numbered as :func:`sinnet_from_shape` numbers them.
    """
    lines, joins, _ = shape_diagram(outline)
    sides: dict[int, set[int]] = {}
    for line, spaces in enumerate(joins):
        for end, space in enumerate(spaces):
            point = np.asarray(lines[line].ends[end])
            sides.setdefault(space, set()).add(_round_the_outline(outline, point)[1])
    alone = [
        space
        for space, on in sides.items()
        if len(on) == 1 and sum(other == on for other in sides.values()) == 1
    ]
    return sorted({space for space, on in sides.items() if len(on) > 1} | set(alone))


def shape_tracks(moves: Sequence[tuple[int, int]]) -> list[list[int]]:
    """The tracks of a sinnet's moves: the curves the book draws, each line
    turning at a bight into the next, the way the moves run.  Every space
    giving once and receiving once, each move leads to the one from the
    space it ends in, and round to where it started.

    Args:
        moves: The moves of a cycle, every space giving and receiving once.

    Returns:
        Each track's moves, by index, in the order they follow each other,
        the track with the first move first.
    """
    gives = {a: k for k, (a, _) in enumerate(moves)}
    tracks: list[list[int]] = []
    seen: set[int] = set()
    for k in range(len(moves)):
        track = []
        while k not in seen:
            seen.add(k)
            track.append(k)
            k = gives[moves[k][1]]
        if track:
            tracks.append(track)
    return tracks


def sinnet_from_shape(
    outline: Sequence[tuple[float, float]],
    extra: Optional[Sequence[int]] = None,
    turned: Sequence[int] = (),
    order: str = "book",
) -> AshleySolidSinnet:
    """The sinnet the book's method makes of a shape.

    Lines cross the shape parallel to its sides (:func:`shape_lines`), and at
    the outline each turns, in a bight, into the next: two lines meeting the
    outline at one point into each other, others into their neighbour on the
    same side.  The bights are the spaces, numbered anticlockwise from the
    one nearest the first corner, and each line is a move between the two
    it joins.

    The moves are made in the book's order: from space 1, along the line
    across the first side if one starts there; then each from the space
    beside where the last ended, one back, then one on, and so on, along the
    line parallel to the last while there is one there, across the shape
    and back; a space that has given its strand gives none again, and its
    line is taken towards it.  The moves of any track
    (:func:`shape_tracks`) may be made the other way round: every space
    still gives once and receives once.  Each space starts with the fewest
    strands the order lets it (:func:`least_counts`), and any ``extra``:
    the book adds strands at the corners of a shape to sharpen its edges.

    Args:
        outline: The shape's corners, anticlockwise, in spacings
            between lines; the first is where the numbering starts, the
            book's bottom left.
        extra: Strands to add to each space, space 1 first; none if None.
        turned: The tracks made the other way round, numbered from 1 as
            :func:`shape_tracks` lists them.
        order: "book", the book's order; or "spaces", space by space, as
            the book makes the moves where it cannot alternate them.

    Returns:
        The sinnet.

    Raises:
        ValueError: If the lines cannot be made into moves in that order.
    """
    lines, joins, bights = shape_diagram(outline)
    n = len(bights)
    corners = np.asarray(outline, dtype=float)
    first_side = corners[1] - corners[0]
    first_side_direction = next(
        (
            line.direction
            for line in lines
            if abs(
                abs(np.dot(np.subtract(line.ends[1], line.ends[0]), first_side))
                - math.dist(*line.ends) * float(np.linalg.norm(first_side))
            )
            < SAME_POINT
        ),
        -1,
    )
    moves = _in_order(
        n, joins, [line.direction for line in lines], first_side_direction, order
    )
    tracks = shape_tracks(moves)
    for track in turned:
        if not 1 <= track <= len(tracks):
            raise ValueError(f"No track {track}: the shape has {len(tracks)}.")
        for k in tracks[track - 1]:
            moves[k] = (moves[k][1], moves[k][0])
    counts = least_counts(moves, n)
    if extra is not None:
        counts = [c + e for c, e in zip(counts, extra)]
    return AshleySolidSinnet(counts, moves)


# ------------------------------------------------------------- to a shape


@dataclass(frozen=True)
class MoveGroups:
    """A sinnet's moves grouped by the direction of their lines: what stays
    the same, whatever the size, for shapes drawn on the same principle
    (:func:`move_groups`).

    Args:
        n_spaces: The spaces round the stand.
        groups: For each direction, its angle from the first, as a share of
            a half turn, and the moves made along it.
    """

    n_spaces: int
    groups: tuple[tuple[Fraction, int], ...]

    @property
    def angles(self) -> list[float]:
        """Each direction's angle from the first."""
        return [math.pi * float(turn) for turn, _ in self.groups]

    @property
    def lines(self) -> list[int]:
        """The moves made along each direction."""
        return [count for _, count in self.groups]

    @property
    def family(self) -> tuple[tuple[Fraction, Fraction], ...]:
        """Each direction's angle, and its moves as a share of the spaces:
        the same for a shape drawn on the same principle at any size, as
        every triangle of :func:`triangle` is, its three directions a third
        of a half turn apart, each with a third of the moves."""
        return tuple(
            (turn, Fraction(count, self.n_spaces)) for turn, count in self.groups
        )


def _cross(first: tuple[int, int], second: tuple[int, int]) -> bool | None:
    """Whether two moves' lines cross; None if they share a space, which
    says nothing, every space being the end of two lines."""
    a, b = sorted(first)
    if {a, b} & set(second):
        return None
    return (a < second[0] < b) != (a < second[1] < b)


def _apart(moves: Sequence[tuple[int, int]]) -> list[list[int]] | None:
    """The moves in sets none of whose lines cross, joining any two that do
    not, or that join the same two spaces, and then any two sets with no
    line of one crossing a line of the other; None unless that leaves two sets
    or more, in each of which no two lines cross."""
    sets = [{k} for k in range(len(moves))]
    for i, j in itertools.combinations(range(len(moves)), 2):
        same = sorted(moves[i]) == sorted(moves[j])
        if same or _cross(moves[i], moves[j]) is False:
            joined = next(s for s in sets if i in s) | next(s for s in sets if j in s)
            sets = [s for s in sets if i not in s and j not in s] + [joined]
    # Two lines meeting in a bight say nothing: sets none of whose lines
    # cross are one direction too, as the two lines of a loop.
    while pair := next(
        (
            (p, q)
            for p, q in itertools.combinations(sets, 2)
            if not any(_cross(moves[i], moves[j]) for i in p for j in q)
        ),
        None,
    ):
        sets = [s for s in sets if s not in pair] + [pair[0] | pair[1]]
    if len(sets) < 2 or any(
        _cross(moves[i], moves[j])
        for s in sets
        for i, j in itertools.combinations(s, 2)
    ):
        return None
    return [sorted(s) for s in sets]


def move_groups(moves: Sequence[tuple[int, int]]) -> MoveGroups:
    """A sinnet's moves grouped by the direction of their lines (see
    :class:`MoveGroups`).

    Lines of one direction never cross.  Where joining every two moves whose
    lines do not cross leaves sets in which none do, as across an oblong,
    those sets are the directions, taken as evenly spread (at right angles
    for two).  Otherwise, as across a triangle, whose lines of different
    directions miss each other near its corners, the directions are found
    from the spaces' numbers: round a stand of ``n`` spaces evenly spaced,
    the line from space ``a`` to space ``b`` runs at ``(a + b) π / n`` and
    a half turn, so moves whose spaces add up to the same number, modulo
    ``n``, are parallel.  Wherever the numbering starts, or whichever way it
    runs, the directions only turn together, and are kept turned as little
    as can be.

    Args:
        moves: The moves, each space giving and receiving once.

    Returns:
        The groups.
    """
    n = len(moves)
    apart = _apart(moves)
    if apart is not None:
        counts = sorted(len(s) for s in apart)
        return MoveGroups(
            n, tuple((Fraction(k, len(counts)), c) for k, c in enumerate(counts))
        )
    sums: dict[int, int] = {}
    for a, b in moves:
        sums[(a + b) % n] = sums.get((a + b) % n, 0) + 1
    # Starting the numbering a space on adds two to every sum; numbering
    # the other way round sends a sum s to 2 - s.
    turned = min(
        tuple(sorted(((sense * s + 2 * shift) % n, c) for s, c in sums.items()))
        for shift in range(n)
        for sense in (1, -1)
    )
    return MoveGroups(n, tuple((Fraction(s, n), c) for s, c in turned))


def oblong(width: int, height: int) -> list[tuple[float, float]]:
    """An oblong (a square if ``width == height``), in spacings between
    lines, from its bottom left corner: ``height`` lines across it,
    ``width`` up it."""
    return [
        (0.0, 0.0),
        (float(width), 0.0),
        (float(width), float(height)),
        (0.0, float(height)),
    ]


def regular_polygon(sides: int, lines_per_side: int) -> list[tuple[float, float]]:
    """A regular polygon of an odd number of sides standing on one, with so
    many lines parallel to each side, the farthest a spacing from the
    corner opposite, from its bottom left corner.

    Args:
        sides: Its sides, odd: with an even number they are parallel in
            pairs, a shape of :func:`_parallel_sided`.
        lines_per_side: Lines parallel to each side.

    Returns:
        Its corners, anticlockwise, in spacings between lines.
    """
    if sides < 3 or sides % 2 == 0:
        raise ValueError(f"a regular polygon of {sides} sides has no corner opposite")
    height = lines_per_side + FIRST_LINE
    radius = height / (1 + math.cos(math.pi / sides))
    first = -math.pi / 2 - math.pi / sides
    corners = [
        (
            radius * math.cos(first + 2 * math.pi * k / sides),
            radius * math.sin(first + 2 * math.pi * k / sides),
        )
        for k in range(sides)
    ]
    x0, y0 = corners[0]
    return [(x - x0, y - y0) for x, y in corners]


def triangle(lines_per_side: int) -> list[tuple[float, float]]:
    """A triangle standing on its base, as the book draws #3045, #3047 and
    #3051 (2, 4 and 6 lines a side): see :func:`regular_polygon`."""
    return regular_polygon(3, lines_per_side)


# ------------------------------------------------------------- on a grid

# The grids a shape is drawn on, its cells: squares, Ashley's lines running
# across and up; or triangles, his lines in three directions a third of a
# half turn apart.  Either way the lines run a spacing apart, through the
# grid's points, and the outline half a spacing beyond the cells.
GRIDS = ("square", "triangle")
# The height of a row of triangles, a spacing, and so the side of one.
TRIANGLE_SIDE = 2 / math.sqrt(3)

# A cell: on the square grid, its bottom left point (i, j); on the
# triangular one, the point (i, j) and 0 for the triangle pointing up from
# it, 1 for the one pointing down beside it.
Cell = tuple[int, ...]


def _grid_point(grid: str, node: tuple[int, int]) -> np.ndarray:
    """Where a grid's point is, in spacings."""
    i, j = node
    if grid == "square":
        return np.array([float(i), float(j)])
    return np.array([(i + j / 2) * TRIANGLE_SIDE, float(j)])


def _cell_points(grid: str, cell: Cell) -> list[tuple[int, int]]:
    """A cell's corners, as grid points, anticlockwise."""
    if grid == "square":
        i, j = cell
        return [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
    i, j, down = cell
    if down:
        return [(i + 1, j), (i + 1, j + 1), (i, j + 1)]
    return [(i, j), (i + 1, j), (i, j + 1)]


def cell_outline(grid: str, cell: Cell) -> list[tuple[float, float]]:
    """A cell's corners, anticlockwise, in spacings."""
    return [_point(_grid_point(grid, node)) for node in _cell_points(grid, cell)]


def grid_outline(grid: str, cells: Sequence[Cell]) -> list[tuple[float, float]]:
    """The outline of a shape made of a grid's cells: round them, half a
    spacing beyond (``FIRST_LINE``), each side of it parallel to one of
    theirs; from its bottom left corner, as the book numbers the spaces.
    Three rows of triangles, three, two and one points across, are the
    book's triangle of three lines a side (:func:`triangle`).

    Args:
        grid: One of ``GRIDS``.
        cells: The cells.

    Returns:
        The outline's corners, anticlockwise, in spacings.

    Raises:
        ValueError: If the cells are not in one piece without holes, or
            meet at a point only.
    """
    if grid not in GRIDS:
        raise ValueError(f"No grid {grid!r}: one of {GRIDS}.")
    if not cells:
        raise ValueError("Give a cell or more.")
    edges = {
        (a, b)
        for cell in set(cells)
        for points in [_cell_points(grid, cell)]
        for a, b in zip(points, points[1:] + points[:1])
    }
    after: dict[tuple[int, int], tuple[int, int]] = {}
    for a, b in edges:
        if (b, a) in edges:
            continue
        if a in after:
            raise ValueError("The cells meet at a point only: join them by a side.")
        after[a] = b
    start = min(
        after, key=lambda node: (_grid_point(grid, node)[1], _grid_point(grid, node)[0])
    )
    loop = [start]
    while after[loop[-1]] != start:
        loop.append(after[loop[-1]])
    if len(loop) != len(after):
        raise ValueError("The cells are in more than one piece, or round a hole.")
    points = [_grid_point(grid, node) for node in loop]
    # Only where the outline turns: points along a side dropped.
    turns = [
        k
        for k in range(len(points))
        if abs(
            _cross2(
                points[k] - points[k - 1], points[(k + 1) % len(points)] - points[k]
            )
        )
        > SAME_POINT
    ]
    points = [points[k] for k in turns]
    outward = []
    for here, there in zip(points, points[1:] + points[:1]):
        along = (there - here) / np.linalg.norm(there - here)
        outward.append((here + FIRST_LINE * np.array([along[1], -along[0]]), along))
    corners = []
    for (p, u), (q, v) in zip(outward[-1:] + outward[:-1], outward):
        t, _ = np.linalg.solve(np.array([u, -v]).T, q - p)
        corners.append(_point(p + t * u))
    return corners


def _cross2(u, v) -> float:
    """The cross product of two vectors in the plane."""
    return float(u[0] * v[1] - u[1] * v[0])


def grid_shape(name: str, size: int, height: int) -> tuple[str, list[Cell]]:
    """A shape to start from, as a grid and its cells.

    Args:
        name: "triangle" or "hexagon", on the triangular grid, ``size``
            lines along each side; "oblong", ``size`` lines across and
            ``height`` up; "L", ``size`` lines across and up, its arms
            ``height`` thick.
        size: Its size, in lines.
        height: Its height, or an L's arms, in lines.

    Returns:
        Its grid and its cells.
    """
    if size < 2 or height < 2:
        raise ValueError("A shape on a grid is two lines or more each way.")
    if name == "triangle":
        return "triangle", [
            (i, j, down)
            for j in range(size)
            for i in range(size)
            for down in (0, 1)
            if i + j + down <= size - 2
        ]
    if name == "hexagon":
        r = size - 1

        def within(node):
            q, t = node
            return max(abs(q), abs(t), abs(q + t)) <= r

        return "triangle", [
            (i, j, down)
            for j in range(-r, r + 1)
            for i in range(-2 * r, 2 * r + 1)
            for down in (0, 1)
            if all(map(within, _cell_points("triangle", (i, j, down))))
        ]
    if name == "oblong":
        return "square", [(i, j) for j in range(height - 1) for i in range(size - 1)]
    if name == "L":
        if height >= size:
            raise ValueError("An L's arms are thinner than it is long.")
        return "square", [
            (i, j)
            for j in range(size - 1)
            for i in range(size - 1)
            if i < height - 1 or j < height - 1
        ]
    raise ValueError(f"No shape {name!r} on a grid.")


def _parallel_sided(groups: MoveGroups) -> list[tuple[float, float]] | None:
    """The shape whose sides are parallel in pairs, one pair to each
    direction of ``groups``, so wide across each that as many lines fit as
    the direction has moves: an oblong for two directions, a hexagon for
    three; None if there is none.

    Across a direction, each pair of sides adds its length times the sine
    of the angle between them: one equation a direction for the sides'
    lengths."""
    angles = np.array(groups.angles)
    if len(angles) < 2:
        return None
    across = np.abs(np.sin(angles[None, :] - angles[:, None]))
    lengths = np.linalg.lstsq(across, np.array(groups.lines, float), rcond=None)[0]
    if np.any(lengths < -SAME_POINT) or not np.allclose(across @ lengths, groups.lines):
        return None
    corners = [np.zeros(2)]
    for angle, length in [*zip(angles, lengths), *zip(angles + math.pi, lengths)]:
        if length > SAME_POINT:
            corners.append(
                corners[-1] + length * np.array([math.cos(angle), math.sin(angle)])
            )
    return [_point(corner) for corner in corners[:-1]]


def _regular(groups: MoveGroups) -> list[tuple[float, float]] | None:
    """The regular polygon of :func:`regular_polygon` with a side to each
    direction of ``groups``, if they are evenly spread and as many lines
    each; None otherwise."""
    sides = len(groups.groups)
    if sides < 3 or sides % 2 == 0 or len(set(groups.lines)) != 1:
        return None
    if any(turn != Fraction(k, sides) for k, (turn, _) in enumerate(groups.groups)):
        return None
    return regular_polygon(sides, groups.lines[0])


@dataclass(frozen=True)
class FoundShape:
    """A shape found for a sinnet's moves (:func:`shapes_from_moves`).

    Args:
        name: What it is: "triangle", "parallel-sided".
        outline: Its corners, anticlockwise, in spacings between lines.
        sinnet: Its own sinnet (:func:`sinnet_from_shape`).
        same_lines: Whether its drawing joins the very spaces the moves
            join, not only lines grouped alike.
    """

    name: str
    outline: tuple[tuple[float, float], ...]
    sinnet: AshleySolidSinnet
    same_lines: bool


def _drawn(moves: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """The lines of a sinnet's moves, whichever way and order they are made,
    and wherever its numbering starts or whichever way it runs round the
    stand: the same for one drawing."""
    n = len(moves)

    def line(a: int, b: int, shift: int, sense: int) -> tuple[int, int]:
        x, y = (sense * (a - 1) + shift) % n + 1, (sense * (b - 1) + shift) % n + 1
        return (x, y) if x < y else (y, x)

    return min(
        tuple(sorted(line(a, b, shift, sense) for a, b in moves))
        for shift in range(n)
        for sense in (1, -1)
    )


def shapes_from_moves(moves: Sequence[tuple[int, int]]) -> list[FoundShape]:
    """The shapes drawn on the principle of a sinnet's moves, at its size,
    made from their groups (:func:`move_groups`), not searched for.

    Each direction of lines is a side, or a pair of parallel sides, of the
    shape, as far across as its moves need: a regular polygon of an odd
    number of sides (:func:`regular_polygon`) where the directions are
    evenly spread with as many moves each, and the shape with sides
    parallel in pairs (an oblong, a hexagon).  Each is kept if its own
    sinnet's moves group alike.

    Args:
        moves: A sinnet's moves, each space giving and receiving once.

    Returns:
        The shapes, those whose drawing joins the same spaces first; none if
        the moves are not drawn so.
    """
    groups = move_groups(moves)
    found = []
    for name, outline in (
        ("regular", _regular(groups)),
        ("parallel-sided", _parallel_sided(groups)),
    ):
        if outline is None:
            continue
        sinnet = sinnet_from_shape(outline)
        if len(sinnet.moves) == len(moves) and move_groups(sinnet.moves) == groups:
            same = _drawn(sinnet.moves) == _drawn(moves)
            found.append(FoundShape(name, tuple(outline), sinnet, same))
    return sorted(found, key=lambda shape: not shape.same_lines)
