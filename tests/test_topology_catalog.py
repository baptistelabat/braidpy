# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids by their topology, each pointing to every way of making it."""

import json

from braidpy import Braid
from braidpy.topology_catalog import (
    Topology,
    braid_of,
    catalogue,
    export,
    for_page,
    load,
    methods,
    related,
    topology_of,
)
from braidpy.web import build


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


def _page(spec):
    """What Braid Studio shows beside a braid, as the page asks for it: the
    description as its address has it, every value a string."""
    spec = {k: str(v) for k, v in spec.items()}
    info = build({**spec, "iterations": 0}, tighten=False)["info"]
    return for_page(spec, info, load(json.loads(json.dumps(export()))))


def test_the_catalogue_is_read_back_as_it_was_written():
    """Braid Studio's copy, written as JSON with the site, is the catalogue."""
    topologies = load(json.loads(json.dumps(export())))
    assert topologies == tuple(entry.make() for entry in catalogue().values())


def test_a_catalogued_braid_is_also_made_as_the_others():
    """The plait's machine, made for three cycles: also made as every other
    way of making the plait, not as itself; and the braids nearest it,
    further on."""
    shown = _page({"source": "machine", "name": "flat_3", "cycles": 3})
    plait = topology_of("machine", "flat_3")
    assert plait is not None
    others = [m.title for m in plait.methods if m.key != "machine:flat_3"]
    assert [m["title"] for m in shown["same"]] == others
    assert "word" in {m["source"] for m in shown["same"]}
    assert len(shown["near"]) == 5
    assert all(m["distance"] > 0 for m in shown["near"])
    distances = [m["distance"] for m in shown["near"]]
    assert distances == sorted(distances)


def test_your_own_braid_is_also_made_on_a_machine():
    """The plait typed from another crossing: also made on the machine."""
    shown = _page({"source": "word", "word": "-2 1", "n_strands": 3, "repeat": 5})
    assert {"source": "machine", "title": "Flat braid, 3 carriers"} in [
        {k: m[k] for k in ("source", "title")} for m in shown["same"]
    ]
    # Opened as much as the page makes of it by default, not one cycle.
    assert all("cycles" not in m["spec"] for m in shown["same"])


def test_a_creeping_disk_braid_is_known_by_its_name():
    """Kongo gumi creeps round the disk: two cycles of it are not its
    pattern, but it is known by its name, and has no braid nearer than
    another of the catalogues."""
    shown = _page({"source": "mobidai", "name": "KONGO_8", "cycles": 2})
    assert shown["same"] == []
    assert len(shown["near"]) == 5


def test_a_braid_with_no_word_has_nothing_shown():
    assert _page({"source": "machine", "name": "soutache_5"}) == {
        "same": [],
        "near": [],
    }


def test_a_tubular_machine_s_braid_is_its_ring_word_filled_in():
    from braidpy.annulus_braid import solid_word

    ring = {"annular_word": "1 -2 3 4", "n_strands": 5}
    assert braid_of(ring) == Braid(tuple(solid_word([1, -2, 3, 4], 4)), 4)
    assert braid_of({"n_strands": 5}) is None
