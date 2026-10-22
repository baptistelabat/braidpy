# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a sinnet on Ashley's stand, found by searching:
braidpy.bridges.ashley."""

from braidpy import Braid
from braidpy.bridges.ashley import ashley_sinnet, sinnet_spec
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
