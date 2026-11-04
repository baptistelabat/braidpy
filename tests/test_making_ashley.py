# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching:
braidpy.making.ashley."""

import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.making.ashley import ashley_moves, ashley_sinnet, sinnet_spec
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
    search = ashley_sinnet(Braid((1, -2, -2, 1) * 3, 3), time_limit=0)
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
