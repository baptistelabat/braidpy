# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching:
braidpy.making.ashley."""

import numpy as np
import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.making.ashley import (
    ashley_moves,
    ashley_sinnet,
    oblong,
    sinnet_spec,
    triangle,
)
from braidpy.ring_program import same_braid
from braidpy.solid_sinnets_catalog import abok_2965, abok_2999


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
    assert same_braid(search.sinnet.braid(1), braid)


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
    assert same_braid(Braid(word, 4), square)


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
    from braidpy import solid_sinnets_catalog as books
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
    from braidpy.solid_sinnets_catalog import abok_3049

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
    from braidpy import solid_sinnets_catalog as books
    from braidpy.making.ashley import sinnet_from_shape

    book = getattr(books, f"abok_{number}")
    n = len(book.initial_counts_per_space)
    edges = [1 if space in ends else 0 for space in range(1, n + 1)]
    made = sinnet_from_shape(oblong(width, 2), extra=edges)
    moves = [tuple(move) for move in book.moves]
    turned = moves.index(made.moves[0])
    assert made.moves == moves[turned:] + moves[:turned]
    assert same_braid(made.braid(), book.braid())


def test_the_square_has_the_book_s_lines_in_the_order_of_the_others():
    """#3070's two loops are the book's; the book moves opposite strands
    together there, 1-3 with 3-1, where the others alternate."""
    from braidpy.making.ashley import sinnet_from_shape
    from braidpy.solid_sinnets_catalog import abok_3070

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
    """A triangle's or an oblong's shape is made again from its moves,
    drawing the very same lines, whatever its size."""
    from braidpy.making.ashley import shapes_from_moves, sinnet_from_shape

    for outline in [triangle(lines) for lines in (3, 4, 12)] + [
        oblong(5, 2),
        oblong(8, 3),
        oblong(12, 7),
    ]:
        found = shapes_from_moves(sinnet_from_shape(outline).moves)
        assert found[0].same_lines
        assert np.allclose(found[0].outline, outline)


@pytest.mark.parametrize("number", [3045, 3047, 3049, 3051, 3059, 3070, 3071, 3072])
def test_the_book_s_moves_find_its_shape(number):
    """The book's triangles and oblongs drawn as the book draws them find
    the shape that draws their lines, however their moves are ordered or
    made, and with whatever strands."""
    from braidpy import solid_sinnets_catalog as books
    from braidpy.making.ashley import shapes_from_moves

    book = getattr(books, f"abok_{number}")
    assert shapes_from_moves(book.moves)[0].same_lines


def test_moves_drawn_otherwise_find_no_shape():
    """A pentagon of four lines a side is not drawn as these shapes are."""
    from braidpy.making.ashley import shapes_from_moves
    from braidpy.solid_sinnets_catalog import abok_3079

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
