# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A horn gear machine written as its graph (braidpy.horn_gear.described)."""

import pytest

from braidpy.annulus_braid import solid_word
from braidpy.braid import Braid
from braidpy.horn_gear import BraidingMachine
from braidpy.horn_gear.described import graph_of, machine_from_graph
from braidpy.horn_gear.word import annular_word, flat_word
from braidpy.machine_catalog import CATALOGUE
from braidpy.similarity import fingerprint, same_fingerprint

# Every machine of the catalogue but the lace machines, whose gears a card
# turns: split gears too.
GEARED = [
    name
    for name, entry in CATALOGUE.items()
    if isinstance(entry.make(), BraidingMachine)
]


def _contacts(machine, gear):
    """A gear's slot at each of its contacts, by the gear it meets there."""
    return {
        (c.gear_b if c.gear_a == gear else c.gear_a): (
            c.slot_a0 if c.gear_a == gear else c.slot_b0
        )
        for c in machine.connections
        if gear in (c.gear_a, c.gear_b)
    }


def _renaming(machine, other):
    """How far round each gear of ``other`` is numbered from ``machine``'s,
    if the two are one machine with their slots named otherwise; None if
    not."""
    turned = {}
    for name, gear in machine.gears.items():
        if (other.gears[name].n_slots, other.gears[name].direction) != (
            gear.n_slots,
            gear.direction,
        ):
            return None
        mine, theirs = _contacts(machine, name), _contacts(other, name)
        found = [
            d
            for d in range(gear.n_slots)
            if all((mine[x] + d) % gear.n_slots == theirs[x] for x in mine)
        ]
        if not found:
            return None
        turned[name] = found[0]
    return turned


def _ring_braid(machine, carriers):
    moves = list(annular_word(machine, carriers=carriers).generators)
    n = max(abs(g) for g in moves)
    return Braid(tuple(solid_word(moves, n)), n)


def test_two_gears_side_by_side():
    machine = machine_from_graph("A-B", n_slots=3)
    assert [(g.name, g.n_slots, g.direction) for g in machine.gears.values()] == [
        ("A", 3, 1),
        ("B", 3, -1),
    ]
    assert [(c.gear_a, c.gear_b) for c in machine.connections] == [("A", "B")]


def test_neighbours_turn_opposite_ways_and_a_gear_may_have_its_own_slots():
    machine = machine_from_graph("A:6-B, A-C; A-D", n_slots=4)
    assert machine.gears["A"].n_slots == 6
    assert {machine.gears[g].n_slots for g in "BCD"} == {4}
    assert {machine.gears[g].direction for g in "BCD"} == {
        -machine.gears["A"].direction
    }
    # Its three contacts as evenly round it as its six slots allow.
    assert sorted(_contacts(machine, "A").values()) == [0, 2, 4]


@pytest.mark.parametrize(
    "text, said",
    [
        ("A-B B-C C-A", "ring of 3"),
        ("A-B C-D", "separate machines"),
        ("A-B A-B", "twice"),
        ("A-A", "itself"),
        ("A B", "Cannot read"),
        ("A:3-B A:4-C", "3 slots and 4"),
        ("A-B A-C A-D A-E A-F", "at least 5"),
        ("", "Give the gears"),
    ],
)
def test_a_graph_that_is_no_machine_is_refused_saying_why(text, said):
    with pytest.raises(ValueError, match=said):
        machine_from_graph(text, n_slots=4)


@pytest.mark.parametrize("name", GEARED)
def test_a_catalogued_machine_written_as_its_graph_is_the_same_machine(name):
    """Read back, the gears, their directions and how far apart their
    contacts are are the catalogue's: the same machine, its slots perhaps
    named from another one round.  But for the ring of four, whose contacts
    the catalogue puts side by side where its geometry has them, and the
    graph as far apart as they go: another machine, the same braid."""
    machine = CATALOGUE[name].make()
    back = machine_from_graph(*graph_of(machine))
    if name == "tubular_8":
        assert same_fingerprint(
            fingerprint(_ring_braid(machine, machine.default_carriers())),
            fingerprint(_ring_braid(back, back.default_carriers())),
        )
    else:
        assert _renaming(machine, back) is not None


@pytest.mark.parametrize("name", ["tubular_12", "flat_3"])
def test_the_same_machine_loaded_alike_makes_the_same_braid(name):
    machine = CATALOGUE[name].make()
    back = machine_from_graph(*graph_of(machine))
    turned = _renaming(machine, back)
    load = machine.default_carriers()
    moved = {
        k: (g, (s + turned[g]) % machine.gears[g].n_slots) for k, (g, s) in load.items()
    }
    if name.startswith("tubular"):
        made = _ring_braid(machine, load), _ring_braid(back, moved)
    else:
        made = (
            Braid(tuple(flat_word(machine, carriers=load)), len(load)),
            Braid(tuple(flat_word(back, carriers=moved)), len(load)),
        )
    assert same_fingerprint(fingerprint(made[0]), fingerprint(made[1]))


def test_graph_of_writes_a_gear_with_other_slots_with_its_own():
    assert graph_of(CATALOGUE["flat_9"].make()) == ("A-B:4 B-C:4 C-D", 5)
    assert graph_of(CATALOGUE["tubular_8"].make()) == ("A-B B-C C-D D-A", 4)


def test_braid_studio_makes_a_machine_of_your_own():
    from braidpy import web
    from braidpy.web.machines import machine_geometry

    spec = {"source": "machine", "name": "custom", "graph": "A-B B-C C-D D-A"}
    made = web.build({**spec, "n_slots": 4, "cycles": 1}, tighten=False)
    assert made["title"].startswith("Your own machine, 4 gears")
    assert len(made["strands"]) == 8
    assert made["info"]["annular_word"] and "collision" not in made["info"]
    # Drawn, and turned by hand, by name.
    drawn = machine_geometry("gears:4:A-B B-C C-D D-A")
    assert [g["name"] for g in drawn["gears"]] == list("ABCD")


def test_braid_studio_draws_each_geared_machine_with_its_graph():
    """Your own starts from the machine drawn before, written as its graph."""
    from braidpy import web
    from braidpy.web.machines import machine_geometry

    entries = {e["name"]: e for e in web.catalogue()["machine"]["entries"]}
    assert entries["custom"]["title"] == "Your own machine…"
    assert machine_geometry("tubular_8")["graph"] == {
        "graph": "A-B B-C C-D D-A",
        "n_slots": 4,
    }
    # Split gears too, joined on their axle.
    assert machine_geometry("twin_plait")["graph"] == {
        "graph": "G0-G1a G1b-G2 G1a+G1b",
        "n_slots": 3,
    }
    # A lace machine, its gears turned by its card, is not.
    assert machine_geometry("lace_dutch")["graph"] is None


# ── Split gears ───────────────────────────────────────────────────────────────


def test_a_split_gear_is_its_parts_on_one_axle():
    """The twin plait: its middle gear of six horns split in two parts of
    three, both turning as one, at one centre, as large as the whole."""
    from braidpy.horn_gear.layout import compute_layout

    machine = machine_from_graph("A-B1 B2-C B1+B2", n_slots=3)
    parts = [machine.gears["B1"], machine.gears["B2"]]
    assert [(g.n_slots, g.size) for g in parts] == [(3, 6), (3, 6)]
    assert parts[0].direction == parts[1].direction == -machine.gears["A"].direction
    centres = compute_layout(machine)
    assert centres["B1"] == centres["B2"]


def test_a_gear_split_in_three_braids_three_plaits_round_it():
    """Its parts' horns take turns round it, so each part's neighbour stands
    where a horn of its own part comes round, and no two parts' carriers
    meet: three plaits, three yarns each."""
    from braidpy import web

    made = web.build(
        {
            "source": "machine",
            "name": "custom",
            "graph": "H1-A H2-B H3-C H1+H2+H3",
            "n_slots": 3,
            "cycles": 1,
        },
        tighten=False,
    )
    assert len(made["strands"]) == 9
    assert "collision" not in made["info"]


def test_a_tree_of_gears_branches_rather_than_piling_up():
    """A gear meshing with three others has them round it, not on top of one
    another; a chain still runs straight along the x-axis."""
    import math

    from braidpy.horn_gear.layout import compute_layout

    star = compute_layout(machine_from_graph("A-B C-B B-D", n_slots=4))
    others = [star[g] for g in "ACD"]
    for i, p in enumerate(others):
        for q in others[i + 1 :]:
            assert math.dist(p, q) > 1.0
    chain = compute_layout(CATALOGUE["flat_9"].make())
    assert all(y == 0.0 for _, y in chain.values())


@pytest.mark.parametrize(
    "text, said",
    [
        ("A-B1 B1+B2", "meshes with no gear"),
        ("A-B1 A-B2 B1+B2", "twice"),
        ("A-B1 B2-C B1+B2 B1+B3", "two axles"),
        ("B1-B2 A-B1 B1+B2", "turn as one"),
        ("A-B1 B2:4-C B1+B2", "as many each"),
    ],
)
def test_a_split_gear_that_cannot_be_is_refused_saying_why(text, said):
    with pytest.raises(ValueError, match=said):
        machine_from_graph(text, n_slots=3)
