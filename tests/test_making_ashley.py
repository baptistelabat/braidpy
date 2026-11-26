# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching:
braidpy.making.ashley."""

import math

import pytest

from braidpy import Braid
from braidpy.braid_catalogue import word_examples
from braidpy.braid_pattern import alike
from braidpy.making.ashley import (
    ashley_moves,
    ashley_sinnet,
    oblong,
    sinnet_spec,
    triangle,
)
from braidpy.solid_sinnets_catalogue import abok_2965, abok_2999


def test_the_plait_is_ashley_s_2965():
    """Found as the book makes it: three strands in two spaces."""
    found = ashley_sinnet(Braid((1, -2) * 6, 3)).sinnet
    assert found is not None
    assert found.initial_counts_per_space == abok_2965.initial_counts_per_space
    assert found.moves == abok_2965.moves


def test_the_square_sinnet_is_ashley_s_2999():
    found = ashley_sinnet(Braid((-1, -2, -2, 3, 2, 2) * 4, 4)).sinnet
    assert found is not None
    assert found.initial_counts_per_space == abok_2999.initial_counts_per_space
    assert sorted(found.moves) == sorted(abok_2999.moves)


def test_a_sinnet_found_makes_the_braid():
    braid = Braid((1, -2, 3, 5, -4) * 2, 6)  # the regular flat braid of 6
    search = ashley_sinnet(braid)
    assert search.sinnet is not None and search.distance == 0
    assert alike(search.sinnet.braid(1), braid)


def test_a_braid_no_sinnet_makes_gets_the_nearest():
    """The weave of 3 is no sinnet of up to three spaces: every one was
    tried, and the nearest is given, with how far it is."""
    search = ashley_sinnet(Braid((1, -2, -2, 1) * 3, 3))
    assert search.sinnet is None and search.complete
    assert search.nearest is not None and search.distance > 0


def test_the_search_stops_at_its_time_limit():
    search = ashley_sinnet(Braid((1, -2, -2, 1) * 3, 3), time_limit_s=0)
    assert not search.complete and search.tried == 0


def test_braid_studio_makes_the_sinnet_found():
    from braidpy.web import build

    square = Braid((-1, -2, -2, 3, 2, 2) * 4, 4)
    sinnet = ashley_sinnet(square).sinnet
    made = build({**sinnet_spec(sinnet), "iterations": 0}, tighten=False)
    word = tuple(int(g) for g in made["info"]["word"].split())
    assert alike(Braid(word, 4), square)


@pytest.mark.parametrize(
    "example",
    [e for e in word_examples() if e.get("layout") != "ring"],
    ids=lambda e: e["title"],
)
def test_any_braid_is_made_one_strand_per_space(example):
    """Exactly the braid, the weave of 3 and the four-strand flat with the
    rest, though no sinnet of the book's kind makes them."""
    n = example["n_strands"]
    braid = Braid(tuple(int(g) for g in example["word"].split()), n)
    made = ashley_moves(braid)
    assert made.initial_counts_per_space == [1, 0] * n
    assert made.braid(1) == braid


def test_each_crossing_puts_every_strand_back_in_its_space():
    for g in (1, -1, 2, -2, 3, -3):
        made = ashley_moves(Braid((g,), 4))
        counts = list(made.initial_counts_per_space)
        for a, b in made.moves:
            assert counts[a - 1], (g, a, b)
            counts[a - 1] -= 1
            counts[b - 1] += 1
        assert counts == made.initial_counts_per_space
        assert len(made.moves) == (4 if g > 0 else 3)


# ------------------------------------------------------------ from a shape


@pytest.mark.parametrize("number, lines", [(3045, 2), (3047, 4), (3051, 6), (3059, 3)])
def test_a_triangle_is_made_as_the_book_makes_it(number, lines):
    """Drawn as the book draws it, a triangle's sinnet is the book's table:
    its moves, in its order, and its strands, the fewest that order lets
    each space start with.  With an odd number of lines a side the moves
    cannot alternate, and are made space by space, as the book makes
    #3059."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import sinnet_from_shape

    book = getattr(books, f"abok_{number}")
    made = sinnet_from_shape(triangle(lines))
    assert made.moves == [tuple(move) for move in book.moves]
    assert made.initial_counts_per_space == book.initial_counts_per_space


def test_a_triangle_with_sharper_edges_has_a_strand_more_at_each_corner():
    """#3049 is #3047's moves with a strand more at each corner of the
    triangle, spaces 1, 5 and 9: "a corner in a diagram represents an
    edge"."""
    from braidpy.making.ashley import sinnet_from_shape
    from braidpy.solid_sinnets_catalogue import abok_3049

    corners = [1 if space in (1, 5, 9) else 0 for space in range(1, 13)]
    made = sinnet_from_shape(triangle(4), extra=corners)
    assert made.moves == [tuple(move) for move in abok_3049.moves]
    assert made.initial_counts_per_space == abok_3049.initial_counts_per_space


@pytest.mark.parametrize("number, width, ends", [(3071, 6, (1, 5)), (3072, 10, (1, 7))])
def test_an_oblong_is_the_book_s_braid(number, width, ends):
    """A flat chisel-edge oblong is the book's cycle of moves, started from
    space 1 where the book starts on the move into it; with a strand more at
    each chisel edge, the two ends of its long loop, it is the book's
    braid."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import sinnet_from_shape

    book = getattr(books, f"abok_{number}")
    n = len(book.initial_counts_per_space)
    edges = [1 if space in ends else 0 for space in range(1, n + 1)]
    made = sinnet_from_shape(oblong(width, 2), extra=edges)
    moves = [tuple(move) for move in book.moves]
    turned = moves.index(made.moves[0])
    assert made.moves == moves[turned:] + moves[:turned]
    assert alike(made.braid(), book.braid())


def test_the_square_has_the_book_s_lines_in_the_order_of_the_others():
    """#3070's two loops are the book's; the book moves opposite strands
    together there, 1-3 with 3-1, where the others alternate."""
    from braidpy.making.ashley import sinnet_from_shape
    from braidpy.solid_sinnets_catalogue import abok_3070

    made = sinnet_from_shape(oblong(2, 2))
    assert sorted(made.moves) == sorted(tuple(move) for move in abok_3070.moves)
    assert made.moves == [(1, 3), (2, 4), (3, 1), (4, 2)]


def test_a_shape_s_lines_run_parallel_to_its_sides():
    """A line half a spacing in from each side, then one a spacing on, as
    many as fit; parallel sides share theirs."""
    from braidpy.making.ashley import shape_diagram

    lines, joins, bights = shape_diagram(oblong(6, 2))
    assert sorted(line.direction for line in lines) == [0, 0] + [1] * 6
    assert len(bights) == 8
    # Every space is the end of two lines: it gives a strand and takes one.
    assert sorted(space for join in joins for space in join) == sorted(
        list(range(1, 9)) * 2
    )


def test_the_fewest_strands_keep_every_space_filled():
    """Two in a space that gives before it is given, one otherwise."""
    from braidpy.making.ashley import least_counts

    assert least_counts([(1, 3), (2, 4), (3, 1), (4, 2)], 4) == [2, 2, 1, 1]


def test_moves_group_alike_for_a_shape_of_any_size():
    """Grouped by the direction of their lines, a triangle's moves are three
    directions a third of a half turn apart, each with a third of the
    moves, however many lines it has; an oblong's two, at right angles,
    each with as many moves as lines fit across it."""
    from fractions import Fraction

    from braidpy.making.ashley import move_groups, sinnet_from_shape

    third = Fraction(1, 3)
    for lines in range(2, 9):
        groups = move_groups(sinnet_from_shape(triangle(lines)).moves)
        assert groups.family == ((0, third), (third, third), (2 * third, third))
    groups = move_groups(sinnet_from_shape(oblong(8, 3)).moves)
    assert groups.groups == ((0, 3), (Fraction(1, 2), 8))


def test_a_shape_comes_back_from_its_moves_at_any_size():
    """A triangle's or an oblong's shape is made again from its moves, on
    its grid, drawing the very same lines, whatever its size."""
    from braidpy.making.ashley import shapes_from_moves, sinnet_from_shape

    for outline, wanted in [
        (triangle(3), ("triangle", "triangle", {3})),
        (triangle(4), ("triangle", "triangle", {4})),
        (triangle(12), ("triangle", "triangle", {12})),
        (oblong(5, 2), ("square", "oblong", {5, 2})),
        (oblong(8, 3), ("square", "oblong", {8, 3})),
        (oblong(12, 7), ("square", "oblong", {12, 7})),
    ]:
        first = shapes_from_moves(sinnet_from_shape(outline).moves)[0]
        assert first.same_lines
        assert first.grid == wanted[0] and first.shape == wanted[1]
        assert first.size in wanted[2]


@pytest.mark.parametrize(
    "grid, shape, size, height",
    [
        ("square", "L", 5, 2),
        ("square", "U", 6, 2),
        ("square", "frame", 6, 2),
        ("diagonal", "square", 6, 2),
        ("triangle", "hexagon", 3, 2),
    ],
)
def test_a_shape_on_a_grid_comes_back_from_its_moves(grid, shape, size, height):
    """An L, a U, a hollow square, a square on a corner and a hexagon come
    back from their moves alone, as the shape they were made of."""
    from braidpy.making.ashley import (
        grid_lines,
        grid_outline,
        grid_shape,
        shapes_from_moves,
        sinnet_from_shape,
    )

    outline, *holes = grid_outline(grid, grid_shape(grid, shape, size, height))
    made = sinnet_from_shape(outline, holes=holes, across=grid_lines(grid))
    first = shapes_from_moves(made.moves)[0]
    assert first.same_lines
    assert (first.grid, first.shape, first.size, first.height) == (
        grid,
        shape,
        size,
        height,
    )


@pytest.mark.parametrize(
    "number", [3045, 3047, 3049, 3051, 3059, 3070, 3071, 3072, 3073, 3074, 3075]
)
def test_the_book_s_moves_find_its_shape(number):
    """The book's triangles and oblongs drawn as the book draws them find
    the shape that draws their lines, however their moves are ordered or
    made, and with whatever strands."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import shapes_from_moves

    book = getattr(books, f"abok_{number}")
    assert shapes_from_moves(book.moves)[0].same_lines


def test_moves_drawn_otherwise_find_no_shape():
    """A pentagon of four lines a side is not drawn as these shapes are."""
    from braidpy.making.ashley import shapes_from_moves
    from braidpy.solid_sinnets_catalogue import abok_3079

    assert shapes_from_moves(abok_3079.moves) == []


def test_a_shape_s_tracks_can_be_turned_round():
    """A triangle of four lines a side is drawn as three tracks; turned
    round, a track's moves go the other way, every space still giving once
    and receiving once."""
    from braidpy.making.ashley import shape_tracks, sinnet_from_shape

    made = sinnet_from_shape(triangle(4))
    tracks = shape_tracks(made.moves)
    assert sorted(len(track) for track in tracks) == [3, 3, 6]
    turned = sinnet_from_shape(triangle(4), turned=[2])
    for k, (a, b) in enumerate(made.moves):
        assert turned.moves[k] == ((b, a) if k in tracks[1] else (a, b))
    every = list(range(1, 13))
    assert sorted(a for a, _ in turned.moves) == every
    assert sorted(b for _, b in turned.moves) == every
    with pytest.raises(ValueError, match="No track"):
        sinnet_from_shape(triangle(4), turned=[4])


@pytest.mark.parametrize(
    "number, outline",
    [(3049, triangle(4)), (3071, oblong(6, 2)), (3072, oblong(10, 2))],
)
def test_the_book_s_strands_more_are_at_the_corners(number, outline):
    """The spaces where the book adds strands are a shape's corners: its
    bights turning a corner, or alone on a side."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import corner_spaces, sinnet_from_shape

    book = getattr(books, f"abok_{number}")
    n = len(book.initial_counts_per_space)
    corners = corner_spaces(outline)
    made = sinnet_from_shape(
        outline, extra=[int(s in corners) for s in range(1, n + 1)]
    )
    assert sorted(made.initial_counts_per_space) == sorted(
        book.initial_counts_per_space
    )
    assert alike(made.braid(1), book.braid(1))


def test_a_shape_on_a_grid_is_drawn_as_the_book_draws_it():
    """Rows of triangles on the triangular grid, outlined half a spacing
    beyond, are the book's triangles, line for line; squares, its
    oblongs."""
    from braidpy.making.ashley import grid_outline, grid_shape, sinnet_from_shape

    for lines in range(2, 7):
        (outline,) = grid_outline(
            "triangle", grid_shape("triangle", "triangle", lines, 2)
        )
        on_grid = sinnet_from_shape(outline)
        assert on_grid == sinnet_from_shape(triangle(lines))
    (outline,) = grid_outline("square", grid_shape("square", "oblong", 10, 2))
    on_grid = sinnet_from_shape(outline)
    assert on_grid.moves == sinnet_from_shape(oblong(10, 2)).moves


def test_a_skewed_shape_without_its_halfway_lines_is_the_square_one():
    """Skewed, a shape keeps its lines' order round the outline: without
    the lines halfway, it makes the square grid's sinnet."""
    from braidpy.making.ashley import grid_outline, grid_shape, sinnet_from_shape

    for shape, size, height in (("oblong", 3, 5), ("L", 5, 2), ("frame", 6, 2)):
        square, *square_holes = grid_outline(
            "square", grid_shape("square", shape, size, height)
        )
        skew, *skew_holes = grid_outline(
            "skew", grid_shape("skew", shape, size, height)
        )
        assert (
            sinnet_from_shape(skew, holes=skew_holes).moves
            == sinnet_from_shape(square, holes=square_holes).moves
        )


@pytest.mark.parametrize("size, height", [(2, 2), (3, 5), (4, 6), (3, 8), (6, 3)])
def test_lines_halfway_end_between_the_others_and_cross_one(size, height):
    """A parallelogram of a by b lines has a + b - 2 more halfway between
    their crossings, the two at its corners crossing nothing left out:
    each meets the outline between two lines' ends, and crosses a line."""
    from braidpy.making.ashley import (
        _crossing,
        grid_halfway,
        grid_outline,
        grid_shape,
        shape_lines,
    )

    (outline,) = grid_outline("skew", grid_shape("skew", "oblong", size, height))
    lines = shape_lines(outline, halfway=grid_halfway("skew"))
    halfway = [
        line for line in lines if line.direction == max(ln.direction for ln in lines)
    ]
    others = [line for line in lines if line not in halfway]
    assert (len(others), len(halfway)) == (size + height, size + height - 2)
    ends = {end for line in others for end in line.ends}
    for line in halfway:
        assert not any(
            math.dist(end, other) < 1e-6 for end in line.ends for other in ends
        )
        assert any(_crossing(line, other) for other in others)


def test_lines_halfway_need_lines_two_ways():
    """Halfway between the crossings of a triangle's three ways: no."""
    from braidpy.making.ashley import shape_lines

    with pytest.raises(ValueError, match="two ways"):
        shape_lines(triangle(3), halfway=0.0)


def test_a_line_is_cut_where_the_outline_turns_back():
    """Across a U, a line through both arms is two lines, one an arm."""
    from braidpy.making.ashley import grid_outline, shape_lines

    u = [(i, j) for i in range(4) for j in range(3) if not (i in (1, 2) and j > 0)]
    lines = shape_lines(*grid_outline("square", u))
    upper = [line for line in lines if line.ends[0][1] == line.ends[1][1] > 1]
    assert len(upper) == 4  # two rows, each cut in two


def test_space_by_space_is_the_book_s_other_order():
    """Made space by space, a triangle of two lines a side is the book's
    #3057 and #3058."""
    from braidpy.making.ashley import sinnet_from_shape
    from braidpy.solid_sinnets_catalogue import abok_3057

    made = sinnet_from_shape(triangle(2), order="spaces")
    assert made.moves == [tuple(move) for move in abok_3057.moves]
    assert made.initial_counts_per_space == abok_3057.initial_counts_per_space


def test_cells_must_make_one_piece():
    from braidpy.making.ashley import grid_outline

    with pytest.raises(ValueError, match="point only"):
        grid_outline("square", [(0, 0), (1, 1)])
    with pytest.raises(ValueError, match="more than one piece"):
        grid_outline("square", [(0, 0), (2, 0)])


def test_a_hollow_square_s_spaces_alternate_round_the_stand():
    """Round a hollow square, the bights of its outline and of its hole are
    numbered together, by the way they lie from the middle: a line across
    a side, from the outline to the hole, joins two spaces side by side, as
    round a tube, every space still giving once and taking once."""
    from braidpy.making.ashley import grid_outline, grid_shape, sinnet_from_shape

    outline, hole = grid_outline("square", grid_shape("square", "frame", 6, 2))
    made = sinnet_from_shape(outline, holes=[hole])
    n = len(made.initial_counts_per_space)
    every = list(range(1, n + 1))
    assert sorted(a for a, _ in made.moves) == every
    assert sorted(b for _, b in made.moves) == every
    across = [(a, b) for a, b in made.moves if (a - b) % n in (1, n - 1)]
    assert len(across) >= 8
    assert made.braid(1).n_strands == made.n_strands


@pytest.mark.parametrize(
    "number, shape, size, height",
    [(3073, "square", 6, 2), (3074, "square", 8, 2), (3075, "oblong", 10, 2)],
)
def test_a_shape_on_its_corner_has_the_book_s_lines(number, shape, size, height):
    """On the diagonal grid, a square or an oblong standing on a corner,
    its lines across and up, is drawn as the book draws #3073, #3074 and
    #3075: the same spaces joined, if not in the same order."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import (
        _drawn,
        grid_lines,
        grid_outline,
        grid_shape,
        sinnet_from_shape,
    )

    book = getattr(books, f"abok_{number}")
    outline, *holes = grid_outline(
        "diagonal", grid_shape("diagonal", shape, size, height)
    )
    made = sinnet_from_shape(outline, holes=holes, across=grid_lines("diagonal"))
    assert _drawn(made.moves) == _drawn([tuple(move) for move in book.moves])


@pytest.mark.parametrize(
    "name",
    sorted(__import__("braidpy.solid_sinnets_catalogue", fromlist=["DRAWN"]).DRAWN),
)
def test_the_book_s_sinnets_are_drawn_as_the_catalogue_says(name):
    """Each of the book's sinnets the catalogue says a shape draws: the
    shape draws its lines, and makes its braid where it says so."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.making.ashley import (
        _drawn,
        corner_spaces,
        grid_halfway,
        grid_lines,
        grid_outline,
        grid_shape,
        sinnet_from_shape,
    )

    drawn = books.DRAWN[name]
    book = getattr(books, name)
    grid = str(drawn["grid"])
    cells = grid_shape(
        grid, str(drawn["shape"]), int(drawn["size"]), int(drawn.get("height", 2))
    )
    outline, *holes = grid_outline(grid, cells)
    across = grid_lines(grid)
    halfway = grid_halfway(grid)
    corners = corner_spaces(outline, holes, across, halfway)
    n = len(book.initial_counts_per_space)
    made = sinnet_from_shape(
        outline,
        extra=[int(drawn.get("corners", 0)) * (s in corners) for s in range(1, n + 1)],
        order=str(drawn.get("order", "book")),
        holes=holes,
        across=across,
        halfway=halfway,
    )
    assert _drawn(made.moves) == _drawn([tuple(move) for move in book.moves])
    if drawn["makes"]:
        assert alike(made.braid(1), book.braid(1))


@pytest.mark.parametrize("name", ["abok_3047", "abok_3059"])
def test_moves_whose_lines_do_not_cross_can_be_made_either_way_round(name):
    """Two moves made one after the other, swapped: the same braid exactly
    when their lines in Ashley's diagram do not cross, another when they
    do.  A group of parallel lines is so moves made in any order."""
    from braidpy import solid_sinnets_catalogue as books
    from braidpy.ashley_solid_sinnet import AshleySolidSinnet
    from braidpy.making.ashley import _cross

    sinnet = getattr(books, name)
    moves = list(sinnet.moves)
    braid = sinnet.braid(1)
    for k in range(len(moves) - 1):
        crossing = _cross(moves[k], moves[k + 1])
        if crossing is None:
            continue
        swapped = moves[:k] + [moves[k + 1], moves[k]] + moves[k + 2 :]
        other = AshleySolidSinnet(list(sinnet.initial_counts_per_space), swapped)
        assert (other.braid(1) == braid) == (not crossing), (k, moves[k], moves[k + 1])
