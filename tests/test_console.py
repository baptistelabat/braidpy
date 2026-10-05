# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Working a machine a step at a time, as the console page does."""

import json
import math
import random

import pytest

from braidpy import console
from braidpy.horn_gear.simulation import CollisionError, simulate


def test_every_machine_offered_can_be_built_and_drawn():
    for name in console.machines():
        shape = console.geometry(name)
        assert shape["gears"], name
        assert shape["contacts"], name
        assert shape["title"], name
        # the page sends this over as JSON, so it has to survive the trip
        json.dumps(shape)


def test_an_unknown_machine_says_so():
    with pytest.raises(KeyError, match="no machine called"):
        console.geometry("not_a_machine")


def test_the_geometry_says_where_a_slot_is_without_asking_again():
    """The page works slot angles out itself; this is the contract it uses."""
    from braidpy.horn_gear.layout import carrier_xy, compute_layout, slot_offsets

    name = "tubular_8"
    machine = console.machines()[name]()
    shape = console.geometry(name)
    layout = compute_layout(machine)
    offsets = slot_offsets(machine, layout)
    riding = {g["name"]: g["ride"] for g in shape["gears"]}

    for gear in shape["gears"]:
        for slot in range(gear["slots"]):
            for time in (0, 1, 5):
                # the gear turns `direction` slots per step; the slot index
                # itself is not mirrored
                angle = (
                    gear["offset"]
                    + 2 * math.pi * (slot + gear["direction"] * time) / gear["slots"]
                )
                mine = (
                    gear["x"] + gear["ride"] * math.cos(angle),
                    gear["y"] + gear["ride"] * math.sin(angle),
                )
                theirs = carrier_xy(
                    machine, layout, offsets, riding, (gear["name"], slot), time
                )
                assert mine == pytest.approx(theirs, abs=1e-9), (gear["name"], slot)


def test_a_step_moves_the_carriers_the_way_the_machine_does():
    name = "tubular_8"
    machine = console.machines()[name]()
    places = console.suggested_loading(name)
    out = console.advance(name, places, 0)
    assert out["time"] == 1
    expected = [list(machine.next_position(p, 0)) for p in places]
    assert out["carriers"] == expected


def test_two_carriers_in_one_slot_are_reported_before_anything_moves():
    found = console.trouble("tubular_8", [["A", 0], ["A", 0]])
    assert len(found) == 1
    assert found[0]["gear"] == "A"
    assert found[0]["slot"] == 0
    assert found[0]["carriers"] == [0, 1]


def test_two_carriers_either_side_of_a_contact_are_reported_too():
    """The rule a carrier dropped on a slot by hand most often breaks."""
    machine = console.machines()["tubular_8"]()
    conn = machine.connections[0]
    slot_a = machine.slot_at_connection(conn.gear_a, conn.slot_a0, 0)
    slot_b = machine.slot_at_connection(conn.gear_b, conn.slot_b0, 0)
    found = console.trouble("tubular_8", [[conn.gear_a, slot_a], [conn.gear_b, slot_b]])
    assert found, "both sides of a contact is a collision"
    assert {(f["gear"], f["slot"]) for f in found} == {
        (conn.gear_a, slot_a),
        (conn.gear_b, slot_b),
    }


def test_an_empty_machine_is_never_in_trouble():
    assert console.trouble("tubular_8", []) == []
    assert console.collisions("tubular_8", [], steps=20) == []


def test_the_suggested_loading_runs_cleanly():
    for name in console.machines():
        places = console.suggested_loading(name)
        assert places, name
        assert console.collisions(name, places, steps=40) == [], name


@pytest.mark.parametrize("name", ["tubular_8", "flat_9", "multiband_10_15_10"])
def test_the_console_agrees_with_the_simulator(name):
    """Whatever the console says about a loading, simulate says the same."""
    machine = console.machines()[name]()
    places = [
        (gear_name, slot)
        for gear_name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    rng = random.Random(0)
    for _ in range(40):
        picked = rng.sample(places, rng.randrange(1, min(10, len(places))))
        mine = bool(console.collisions(name, picked, steps=30))
        try:
            simulate(machine, 30, dict(enumerate(picked)))
            theirs = False
        except CollisionError:
            theirs = True
        assert mine == theirs, picked


def test_a_collision_says_which_step_it_happens_at():
    machine = console.machines()["tubular_8"]()
    places = [
        (gear_name, slot)
        for gear_name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    found = console.collisions("tubular_8", places, steps=30)
    assert found, "a full machine must collide"
    assert all("step" in item for item in found)
    assert min(item["step"] for item in found) >= 0


def test_the_switched_contacts_are_marked_for_the_drawing():
    shape = console.geometry("multiband_10_15_10")
    switched = {c["name"] for c in shape["contacts"] if c["switched"]}
    assert switched == {"G3-G4", "G4-G5", "G10-G11", "G11-G12"}
    plain = [c for c in shape["contacts"] if not c["switched"]]
    assert plain, "most contacts are not switched"
