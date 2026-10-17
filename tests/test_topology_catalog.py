# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids by their topology, each pointing to every way of making it."""

from braidpy import Braid
from braidpy.topology_catalog import (
    Topology,
    catalogue,
    methods,
    related,
    topology_of,
)


def test_the_plait_is_made_three_ways():
    """A braid word, the Dutch braid — the plait seen from behind — and a
    three-carrier flat braiding machine all make the plait."""
    plait = topology_of("machine", "flat_3")
    assert plait is not None
    assert {m.key for m in plait.methods} == {
        "word:flat3",
        "word:inverted_flat3",
        "machine:flat_3",
    }


def test_each_way_points_back_to_its_topology():
    """The link is two ways: a topology lists its methods, and each method
    finds that topology again."""
    for entry in catalogue().values():
        topology = entry.make()
        assert isinstance(topology, Topology)
        for method in topology.methods:
            assert topology_of(method.source, method.name) == topology


def test_every_braid_word_is_in_exactly_one_topology():
    listed = [m.key for entry in catalogue().values() for m in entry.make().methods]
    assert len(listed) == len(set(listed))
    # Machines braiding round cores have no braid word of their strands.
    assert topology_of("machine", "soutache_5") is None
    left_out = {m.key for m in methods()} - set(listed)
    assert left_out == {"machine:soutache_5", "machine:soutache_7", "machine:princess"}


def test_every_source_is_in_the_catalogue():
    sources = {m.source for entry in catalogue().values() for m in entry.make().methods}
    assert sources == {"word", "kumihimo", "mobidai", "sinnet", "machine"}


def test_your_own_braid_finds_its_topology_and_the_ways_to_make_it():
    """The plait typed from another crossing, repeated more: its topology
    comes first, at distance 0, and with it the machine that makes it."""
    (first, gap), *others = related(Braid([-2, 1] * 7, 3), count=4)
    assert gap < 1e-9
    assert "machine:flat_3" in {m.key for m in first.methods}
    assert len(others) == 3
    assert all(d > 0 for _, d in others)
