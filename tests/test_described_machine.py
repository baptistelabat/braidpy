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
    named from another one round."""
    machine = CATALOGUE[name].make()
    back = machine_from_graph(*graph_of(machine))
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
    take one slot: three plaits, three yarns each.  A carrier leaving for a
    neighbour runs close by the next part's horn coming round to that
    contact, but not to it: the machine has to be large for its bobbins,
    and says how large."""
    from braidpy import web
    from braidpy.horn_gear.take_off import MEET, clearance

    graph = "H1-A H2-B H3-C H1+H2+H3"
    room = clearance(machine_from_graph(graph, 3), 6)
    assert room is not None and room.met is None
    assert MEET < room.share < 0.1
    made = web.build(
        {
            "source": "machine",
            "name": "custom",
            "graph": graph,
            "n_slots": 3,
            "cycles": 1,
        },
        tighten=False,
    )
    assert len(made["strands"]) == 9
    assert "collision" not in made["info"]
    assert any("Sized for bobbins" in note for note in made["notes"])


def test_carriers_at_one_point_stop_a_machine_of_any_size():
    """Two carriers in different slots can still come to one point, as on a
    gear drawn on top of another: scaled up, they stay at one point, so the
    machine stops there."""
    from braidpy.horn_gear.described import DescribedMachine
    from braidpy.horn_gear.layout import compute_layout
    from braidpy.horn_gear.take_off import too_close

    machine = machine_from_graph("A-B B-C", 4)
    at = compute_layout(machine)
    piled = DescribedMachine(
        list(machine.gears.values()), machine.connections, {**at, "C": at["A"]}
    )
    assert too_close(machine, 8) is None
    met = too_close(piled, 8)
    assert met is not None and met.distance < met.limit


def test_a_machine_drawn_larger_keeps_its_carriers_further_apart():
    """Scaled up, every distance between carriers grows alike: bobbins of a
    given size pass on a machine drawn ``scale_for`` times as large."""
    from braidpy.horn_gear.take_off import clearance

    machine = machine_from_graph("A-B B-C C-D D-A", 4)
    small, large = clearance(machine, 8), clearance(machine, 8, scale=2.0)
    assert small is not None and large is not None
    assert large.distance == pytest.approx(2 * small.distance)
    assert large.share == pytest.approx(small.share)
    assert small.scale_for(small.distance * 3) == pytest.approx(3)


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_no_catalogued_machine_brings_two_carriers_to_one_point(name):
    """None is stopped: its carriers clear each other on a machine large
    enough for its bobbins, a horn gap of at most two bobbins across."""
    from braidpy.horn_gear.simulation import state_period
    from braidpy.horn_gear.take_off import clearance

    machine = CATALOGUE[name].make()
    carriers = machine.default_carriers()
    room = clearance(machine, min(state_period(machine, carriers) or 1, 64), carriers)
    if room is not None:
        assert room.met is None
        assert room.share > 0.5


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


# The catalogue's machines as they were built gear by gear, before they were
# written as graphs: each gear's slots and direction, each contact's slots,
# and the gears fed an axial yarn.
_BUILT = {
    "flat_3": ({"A": (3, 1), "B": (3, -1)}, [("A", "B", 0, 0)], ""),
    "flat_4": ({"A": (4, 1), "B": (4, -1)}, [("A", "B", 0, 0)], ""),
    "flat_9": (
        {"A": (5, 1), "B": (4, -1), "C": (4, 1), "D": (5, -1)},
        [("A", "B", 0, 2), ("B", "C", 0, 2), ("C", "D", 0, 0)],
        "",
    ),
    "soutache_5": ({"A": (5, 1), "B": (5, -1)}, [("A", "B", 0, 0)], "AB"),
    "soutache_7": ({"A": (7, 1), "B": (7, -1)}, [("A", "B", 0, 0)], "AB"),
    "princess": (
        {"A": (5, 1), "B": (6, -1), "C": (5, 1)},
        [("A", "B", 0, 0), ("B", "C", 3, 0)],
        "B",
    ),
    "tubular_8": (
        {g: (4, (-1) ** i) for i, g in enumerate("ABCD")},
        [("A", "B", 1, 3), ("B", "C", 0, 3), ("C", "D", 0, 3), ("D", "A", 0, 0)],
        "",
    ),
    "tubular_12": (
        {g: (4, (-1) ** i) for i, g in enumerate("ABCDEF")},
        [(a, b, 1, 3) for a, b in zip("ABCDEF", "BCDEFA")],
        "",
    ),
    "tubular_16": (
        {g: (4, (-1) ** i) for i, g in enumerate("ABCDEFGH")},
        [(a, b, 1, 3) for a, b in zip("ABCDEFGH", "BCDEFGHA")],
        "",
    ),
    "triaxial_16": (
        {g: (4, (-1) ** i) for i, g in enumerate("ABCDEFGH")},
        [(a, b, 1, 3) for a, b in zip("ABCDEFGH", "BCDEFGHA")],
        "ABCDEFGH",
    ),
}


def _built(name):
    from braidpy.horn_gear import Axial, Connection, HornGear

    gears, contacts, fed = _BUILT[name]
    return BraidingMachine(
        [HornGear(g, n, direction=d) for g, (n, d) in gears.items()],
        [Connection(a, b, sa, sb, name=f"{a}-{b}") for a, b, sa, sb in contacts],
        axials=[Axial(f"axial_{g}", (g,)) for g in fed],
    )


@pytest.mark.parametrize("name", list(_BUILT))
def test_a_catalogued_machine_written_as_its_graph_is_the_one_built(name):
    """Written as its graph, each catalogued machine is the one built gear by
    gear, its slots perhaps numbered from another one round, or, a ring that
    hands over between steps, its gears meshing alike: it feeds its axials
    where that one did, and loads itself with as many carriers."""
    built = _built(name)
    machine = CATALOGUE[name].make()
    if any(c.phase for c in machine.connections):
        # A ring that whole slots cannot put on its horns hands over between
        # steps, at other slots than the one built: the same gears turning
        # the same ways, meshing alike.
        assert {
            name: (gear.n_slots, gear.direction) for name, gear in built.gears.items()
        } == {
            name: (gear.n_slots, gear.direction) for name, gear in machine.gears.items()
        }
        assert {frozenset((c.gear_a, c.gear_b)) for c in built.connections} == {
            frozenset((c.gear_a, c.gear_b)) for c in machine.connections
        }
    else:
        assert _renaming(built, machine) is not None
    assert [a.anchor for a in machine.axials] == [a.anchor for a in built.axials]
    assert len(machine.default_carriers()) == len(built.default_carriers())


def _windings(machine):
    """How many times each strand winds round each other over a cycle, as a
    sorted list a strand: the same for one braid, however drawn and
    whichever way its carriers are numbered."""
    from collections import defaultdict
    from itertools import combinations

    import numpy as np

    from braidpy.horn_gear.word import _trajectories

    xy = _trajectories(machine, machine.default_carriers(), None, 64, 1.0).xy
    around = defaultdict(list)
    for a, b in combinations(sorted(xy), 2):
        gap = xy[a] - xy[b]
        angle = np.unwrap(np.arctan2(gap[:, 1], gap[:, 0]))
        turns = round(float((angle[-1] - angle[0]) / (2 * np.pi)), 1)
        around[a].append(turns)
        around[b].append(turns)
    return sorted(sorted(t) for t in around.values())


@pytest.mark.parametrize("name", ["tubular_12", "tubular_16", "triaxial_16"])
def test_a_ring_handing_over_between_steps_makes_the_same_braid(name):
    """A ring of six or eight gears of four slots cannot put a horn on each
    contact at the end of a step: built with whole steps, its contacts
    missed their horns by a third or a quarter of a slot.  Each contact
    hands over when the horns come round to it instead, every contact on a
    horn, and the braid is the same: every strand winds round every other
    as often as on the machine built with whole steps."""
    from braidpy.horn_gear.layout import compute_layout, offset_residuals

    machine, built = CATALOGUE[name].make(), _built(name)
    assert max(offset_residuals(built, compute_layout(built)).values()) > 0.3
    assert max(offset_residuals(machine, compute_layout(machine)).values()) < 1e-3
    assert _windings(machine) == _windings(built)


def test_axials_are_fed_up_a_gear_or_down_a_ring_written_either_way():
    from braidpy.horn_gear import axial_spots
    from braidpy.horn_gear.described import axial_text, axials_of

    ring = "A-B B-C C-D D-E E-F F-G G-H H-A"
    machine = machine_from_graph(ring, axials="C A H-G-F-E-D-C-B-A")
    assert axials_of(machine) == "C A A-B-C-D-E-F-G-H"
    assert [axial_text(s) for s in axial_spots(machine)] == [
        *"ABCDEFGH",
        "A-B-C-D-E-F-G-H",
    ]
    # A split gear's parts share an axle, and so one place for an axial.
    split = machine_from_graph("G0-G1a G1b-G2 G1a+G1b", 3, axials="G1b")
    assert [axial_text(s) for s in axial_spots(split)] == ["G0", "G1a", "G2"]
    assert axials_of(split) == "G1a"


@pytest.mark.parametrize(
    "graph, axials, said",
    [
        ("A-B", "C", "No place for an axial at C"),
        ("A-B B-C", "A-B-C", "No place"),
        ("A-B", "A A", "twice"),
    ],
)
def test_an_axial_where_there_is_no_room_is_refused(graph, axials, said):
    with pytest.raises(ValueError, match=said):
        machine_from_graph(graph, axials=axials)


def test_a_machine_starts_with_the_carriers_it_is_given():
    from braidpy.horn_gear.described import loading_of

    machine = machine_from_graph("A-B B-C C-D D-A", loading="A:1 C:3")
    assert machine.default_carriers() == {0: ("A", 1), 1: ("C", 3)}
    assert loading_of(machine.default_carriers()) == "A:1 C:3"
    for loading, said in [("A:4", "slots 0 to 3"), ("A:1 A:1", "same slot")]:
        with pytest.raises(ValueError, match=said):
            machine_from_graph("A-B", loading=loading)


def test_braid_studio_shows_where_axials_go_and_braids_round_those_loaded():
    from braidpy import web
    from braidpy.web.machines import machine_geometry

    drawn = machine_geometry("tubular_8")
    assert [s["at"] for s in drawn["axials"]] == [*"ABCD", "A-B-C-D"]
    assert drawn["own_axials"] == []
    assert machine_geometry("princess")["own_axials"] == ["B"]
    spec = {"source": "machine", "name": "tubular_8", "cycles": 1}
    made = web.build({**spec, "axials": "A C A-B-C-D"}, tighten=False)
    assert [s["name"] for s in made["strands"]][-3:] == [
        "Core axial_A",
        "Core axial_C",
        "Core core",
    ]
    # Every axial taken off: none, not the machine's own.
    bare = web.build({**spec, "name": "triaxial_16", "axials": "none"}, tighten=False)
    assert not any(s["name"].startswith("Core") for s in bare["strands"])


def test_two_split_gears_may_mesh_once_for_each_pairing_of_their_parts():
    """Two bands side by side on one pair of axles, neither reaching the other.

    Each axle is split in two, and each band has a pair of halves to itself.
    The halves of one axle meet the other axle once each, which is what keeps
    the bands apart: a part meeting one axle twice would let a carrier leave
    by either contact.
    """
    from braidpy.horn_gear.loading import load_carriers
    from braidpy.horn_gear.simulation import simulate
    from braidpy.horn_gear.tracks import compute_tracks, simulation_period

    machine = machine_from_graph("A1-B1 A2-B2 A1+A2 B1+B2", n_slots=4)
    assert sorted(machine.gears) == ["A1", "A2", "B1", "B2"]
    assert [(g.n_slots, g.size) for g in machine.gears.values()] == [(4, 8)] * 4
    assert len(machine.connections) == 2
    # Parts of one axle turn as one, and meshing axles turn opposite ways.
    assert machine.gears["A1"].direction == machine.gears["A2"].direction
    assert machine.gears["B1"].direction == -machine.gears["A1"].direction

    # Every track stays within one band: two gears meeting at one contact
    # shuttle a carrier between one pair of slots, so there are eight of them.
    tracks = compute_tracks(machine)
    assert sorted(len(t) for t in tracks) == [2] * 8
    for track in tracks:
        gears = {gear for gear, _ in track}
        assert gears in ({"A1", "B1"}, {"A2", "B2"})
    loading = load_carriers(machine)
    period = simulation_period(machine)
    history = simulate(machine, period, loading)
    first = {c.carrier_id: c.position for c in history[0].carriers}
    assert first == {c.carrier_id: c.position for c in history[-1].carriers}
    band = {"A1", "B1"}
    inside = {
        c.carrier_id for s in history for c in s.carriers if c.position[0] in band
    }
    outside = {
        c.carrier_id for s in history for c in s.carriers if c.position[0] not in band
    }
    assert not inside & outside


def test_a_part_meeting_one_axle_twice_is_refused():
    """Which is the split undone: the carrier could leave by either contact."""
    with pytest.raises(ValueError, match="A1 and B1\\+B2 are named as meshing twice"):
        machine_from_graph("A1-B1 A1-B2 A2-C A1+A2 B1+B2", n_slots=4)


def test_two_split_gears_meshing_twice_are_written_back_as_they_were():
    """So a machine of your own can be read from the page and written to it."""
    graph = "A1-B1 A2-B2 A1+A2 B1+B2"
    machine = machine_from_graph(graph, n_slots=4)
    written, slots = graph_of(machine)
    again = machine_from_graph(written, slots)
    assert sorted(again.gears) == sorted(machine.gears)
    assert {(c.gear_a, c.gear_b) for c in again.connections} == {
        (c.gear_a, c.gear_b) for c in machine.connections
    }


def test_two_split_gears_meshing_twice_touch_and_hand_over_in_turn():
    """Two split gears meshing twice touch at one contact.  A horn of each
    comes round to it once a pitch, twice a step: the parts named first
    hand over there at the step's end, the others half a step on, at the
    same point.  Each contact is on a horn of each wheel, and each band's
    carriers cross from one wheel to the other."""
    import math

    from braidpy.horn_gear.layout import compute_layout, gear_radii, offset_residuals
    from braidpy.horn_gear.simulation import simulate

    machine = machine_from_graph("A1-B1 A2-B2 A1+A2 B1+B2", n_slots=4)
    layout, radii = compute_layout(machine), gear_radii(machine)
    assert math.dist(layout["A1"], layout["B1"]) == pytest.approx(
        radii["A1"] + radii["B1"]
    )
    assert {c.name: c.phase for c in machine.connections} == {
        "A1-B1": 0.0,
        "A2-B2": 0.5,
    }
    assert max(offset_residuals(machine, layout).values()) < 1e-9
    gears_of: dict = {}
    for state in simulate(machine, 8, machine.default_carriers()):
        for carrier in state.carriers:
            gears_of.setdefault(carrier.carrier_id, set()).add(carrier.gear)
    assert any({"A1", "B1"} <= gears for gears in gears_of.values())
    assert any({"A2", "B2"} <= gears for gears in gears_of.values())


def test_a_carrier_handed_over_half_a_step_in_is_drawn_without_a_jump():
    """Handed over halfway through a step, a carrier is drawn on its new
    wheel from then on, where the old one left it."""
    import math
    from itertools import pairwise

    from braidpy.horn_gear.layout import (
        carrier_radius,
        carrier_xy,
        compute_layout,
        slot_angles,
    )
    from braidpy.horn_gear.simulation import simulate

    machine = machine_from_graph("A1-B1 A2-B2 A1+A2 B1+B2", n_slots=4)
    layout = compute_layout(machine)
    angles = slot_angles(machine, layout)
    riding = {name: carrier_radius(machine, layout, name) for name in machine.gears}
    widest = 0.0
    for state in simulate(machine, 8, machine.default_carriers())[:-1]:
        for carrier in state.carriers:
            points = [
                carrier_xy(
                    machine, layout, angles, riding, carrier.position, state.time, f
                )
                for f in [i / 96 for i in range(97)]
            ]
            widest = max(widest, *(math.dist(p, q) for p, q in pairwise(points)))
    assert widest < 0.2


@pytest.mark.parametrize(
    "graph", ["A1-B1 A2-B2 A1+A2 B1+B2", "X-A1 A1-B1 A2-B2 B2-Y A1+A2 B1+B2"]
)
def test_split_gears_meshing_twice_keep_their_carriers_apart(graph):
    """Touching at one contact, their bands handing over there in turn, two
    split gears meshing twice never bring two carriers together, with gears
    of their own beside them or not: none comes within half the gap between
    two neighbouring horns of another.  When each crossing of their notch
    circles was a hand-over, the other band's horns met there too, and with
    gears beside them two carriers came to the very same point."""
    import math
    from itertools import combinations

    import numpy as np

    from braidpy.horn_gear.layout import gear_radii
    from braidpy.horn_gear.simulation import state_period
    from braidpy.horn_gear.take_off import carrier_trajectories

    machine = machine_from_graph(graph, 4)
    period = state_period(machine, machine.default_carriers())
    tracks = carrier_trajectories(machine, period, n_substeps=48)
    radii = gear_radii(machine)
    gap = min(
        2 * radii[name] * math.sin(math.pi / (gear.size or gear.n_slots))
        for name, gear in machine.gears.items()
    )
    closest = min(
        float(np.min(np.linalg.norm(tracks.xy[a] - tracks.xy[b], axis=1)))
        for a, b in combinations(tracks.xy, 2)
    )
    assert closest > gap / 2


# Ladders of gears: of two sizes, alike, and of two sizes with split gears
# in the middle, which was laid out with its rungs a third as long as they
# should be.
LADDERS = [
    "A0-A1:3 A1-A2 B0-B1:3 B1-B2 A0-B0 A1-B1 A2-B2",
    "A0-A1 A1-A2 B0-B1 B1-B2 A0-B0 A1-B1 A2-B2",
    (
        "A0-A1:3 A0-B0 A1-A2:3 A1-B1:3 A2-A3a A2-B2:3 A3a-B3a B0-B1 B1-B2 B2-B3a "
        "A3b-A4:3 A3b-B3b A4-A5:3 A4-B4:3 A5-A6 A5-B5:3 A6-B6 B3b-B4 B4-B5 B5-B6 "
        "A3a+A3b B3a+B3b"
    ),
]


@pytest.mark.parametrize("graph", LADDERS)
def test_a_matrix_of_gears_touches_and_overlaps_nowhere(graph):
    """Kamada-Kawai's compromise, shrunk till no mesh was too long, left
    every other too short: gears ran through each other.  Relaxed, every
    two axles that mesh touch, and no two others overlap.  The parts of a
    split gear share an axle: two axles mesh if any of their parts do."""
    import math

    from braidpy.horn_gear.layout import CLEARANCE, compute_layout, gear_radii

    machine = machine_from_graph(graph, 4)
    centres, radii = compute_layout(machine), gear_radii(machine)
    # An axle by where it stands: a split gear's parts stand on one.
    meshes = {
        frozenset((centres[c.gear_a], centres[c.gear_b])) for c in machine.connections
    }
    size = {centres[name]: radii[name] for name in centres}
    axles = sorted(size)
    for i, a in enumerate(axles):
        for b in axles[i + 1 :]:
            apart = math.dist(a, b)
            touching = size[a] + size[b]
            if frozenset((a, b)) in meshes:
                assert apart == pytest.approx(touching, rel=0.01)
            else:
                assert apart >= touching * (1 + CLEARANCE) * 0.99


@pytest.mark.slow
def test_the_split_ladder_puts_every_contact_on_a_horn():
    """The split ladder's squares of 3- and 4-slot gears cannot have every
    contact on a horn at the end of a step, their angles adding up to more
    than a turn.  Each contact hands over when the horns come round to it
    instead, the gears moved and sized so that they come round together:
    every contact is on a horn, and the machine runs a whole cycle."""
    from braidpy.horn_gear.layout import compute_layout, offset_residuals
    from braidpy.horn_gear.simulation import simulate, state_period

    machine = machine_from_graph(LADDERS[-1], 4)
    assert max(offset_residuals(machine, compute_layout(machine)).values()) < 1e-3
    assert len({round(c.phase, 3) for c in machine.connections}) > 2
    carriers = machine.default_carriers()
    simulate(machine, state_period(machine, carriers), carriers)


def test_the_timing_takes_no_step_from_two_gears_at_one_place():
    """Two meshing gears started at one place have no direction between
    them: the fit's derivatives divided by their distance, gave a NaN, and
    on some machines the linear solve raised on it.  It takes its step from
    as far apart as SAME_PLACE, and every number stays finite."""
    import math

    import numpy as np

    from braidpy.horn_gear.layout import RingContacts, time_ring

    r = math.sqrt(4)
    centres = np.array([[0.0, 0.0], [0.0, 0.0], [2 * r, 2 * r], [2 * r, 0.0]])
    first, second = np.array([0, 1, 2, 3]), np.array([1, 2, 3, 0])
    turns = np.array([1, -1, 1, -1]) * 4 / (2 * math.pi)
    contacts = RingContacts(first, second, turns, np.zeros(4), np.zeros(4), np.ones(4))
    with np.errstate(all="raise"):
        placed, _, _, phases = time_ring(
            centres,
            np.full(4, r),
            np.full(4, r),
            [(0, 1), (1, 2), (2, 3), (0, 3)],
            [(0, 2), (1, 3)],
            contacts,
        )
    assert np.all(np.isfinite(placed)) and all(map(math.isfinite, phases))


def test_the_timing_damps_harder_where_its_equations_are_singular(monkeypatch):
    """Where the fit's equations are singular, as CI's BLAS once found them
    on a ladder of two sizes, it damps harder and goes on, rather than
    raise: the ladder still has every contact on a horn."""
    import numpy as np

    from braidpy.horn_gear import layout
    from braidpy.horn_gear.layout import compute_layout, offset_residuals

    solve, calls = np.linalg.solve, []

    def singular_once(a, b):
        calls.append(1)
        if len(calls) == 1:
            raise np.linalg.LinAlgError("Singular matrix")
        return solve(a, b)

    monkeypatch.setattr(layout.np.linalg, "solve", singular_once)
    machine = machine_from_graph(LADDERS[0], 4)
    assert len(calls) > 1
    assert max(offset_residuals(machine, compute_layout(machine)).values()) < 1e-3
