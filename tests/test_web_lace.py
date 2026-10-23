# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Jacquard lace machines for the web page: made by their punchcard,
loaded by hand, turned by the handle."""

import pytest

from braidpy import Braid
from braidpy.braid_catalog import CATALOGUE as BRAIDS
from braidpy.horn_gear.jacquard import jacquard_lace_ring
from braidpy.machine_catalog import LACE
from braidpy.making.lace import punchcard_text, ring_braid
from braidpy.pure_braid import repeating_unit
from braidpy.web import build, catalogue, machine_geometry, machine_turned


@pytest.mark.parametrize("name", list(LACE))
def test_every_lace_machine_is_made_and_its_word_read(name):
    result = build({"source": "lace", "name": name, "cycles": 2, "iterations": 0})
    machine = LACE[name].make().machine()
    assert len(result["strands"]) == len(machine.default_carriers())
    assert result["info"]["made"] == 2
    assert result["info"]["word"]
    assert punchcard_text(machine.program) in "\n".join(result["notes"])


@pytest.mark.parametrize(
    ("name", "braid"),
    [
        ("lace_dutch", "inverted_flat3"),
        ("lace_plait", "flat3"),
        ("lace_weave3", "weave3"),
        ("lace_sinnet4", "abok_2974"),
        ("lace_square4", "square4"),
        ("lace_flat6", "regular_flat6"),
    ],
)
def test_a_card_makes_its_catalogue_braid(name, braid):
    """A pass of the card is a repeat of the braid it was punched for."""
    made = BRAIDS[braid].make()
    unit = Braid(
        tuple(repeating_unit([int(g) for g in made.generators])), made.n_strands
    )
    word = build({"source": "lace", "name": name, "iterations": 0})["info"]["word"]
    assert Braid(tuple(int(g) for g in word.split()), made.n_strands) == unit


def test_the_lace_machines_are_a_source_of_their_own():
    listed = catalogue()
    assert [e["name"] for e in listed["lace"]["entries"]] == [*LACE, "custom"]
    assert not set(LACE) & {e["name"] for e in listed["machine"]["entries"]}


def test_a_lace_machine_is_drawn_and_turned_by_hand():
    shape = machine_geometry("lace_plait")
    assert len(shape["gears"]) == 4
    assert shape["loading"] == [["A", 0], ["B", 0], ["C", 0]]
    turned = machine_turned("lace_plait", shape["loading"], 4)
    assert turned["time"] == 4 and turned["met"] == []


def test_a_lace_machine_threaded_by_hand():
    """Two bobbins, the third notch left empty: a braid of two strands."""
    result = build({"source": "lace", "name": "lace_plait", "carriers": "A:0 C:0"})
    assert len(result["strands"]) == 2


def test_bobbins_in_one_notch_cannot_be_braided():
    """A:0 and B:1 are the same notch, seen from either gear."""
    with pytest.raises(ValueError, match="meet as soon as the machine turns"):
        build({"source": "lace", "name": "lace_plait", "carriers": "A:0 B:1"})


def test_a_ring_with_every_gear_turning_is_read_line_by_line():
    """Both lines of a step turn neighbouring gears: the second takes the
    bobbins the first brought, and the reading follows them."""
    machine = jacquard_lace_ring(6)
    braid = ring_braid(machine)
    assert braid.n_strands == 6 and braid.generators


def test_a_ring_threaded_in_some_notches():
    machine = jacquard_lace_ring(6, threaded=[0, 2, 4])
    assert machine.default_carriers() == {0: ("A", 0), 1: ("C", 0), 2: ("E", 0)}


@pytest.mark.parametrize(
    "entry", catalogue()["lace"]["entries"][:-1], ids=lambda e: e["name"]
)
def test_a_catalogued_card_typed_in_as_your_own_is_the_same_braid(entry):
    """Each catalogued machine shows its gears and card, ready to change:
    as they are, they make the same braid."""
    machine = LACE[entry["name"]].make().machine()
    threading = " ".join(f"{g}:{s}" for g, s in machine.default_carriers().values())
    own = {"source": "lace", "name": "custom", "carriers": threading, "iterations": 0}
    made = build({**own, **entry["pattern"]})
    catalogued = build({"source": "lace", "name": entry["name"], "iterations": 0})
    assert made["info"]["word"] == catalogued["info"]["word"]


def test_your_own_card_is_offered_last():
    assert catalogue()["lace"]["entries"][-1] == {
        "name": "custom",
        "title": "Your own card…",
    }


@pytest.mark.parametrize(
    ("n_gears", "card", "message"),
    [
        (5, "10000 01000", "even number"),
        (4, "1000", "two groups"),
        (4, "10x0 0000", "0 and 1"),
        (4, "100 010", "one for each of the 4 gears"),
        (4, "0100 0000", "turns the other way"),
        (4, "", "Give the card"),
    ],
)
def test_a_card_that_cannot_drive_the_machine_says_why(n_gears, card, message):
    with pytest.raises(ValueError, match=message):
        build({"source": "lace", "name": "custom", "n_gears": n_gears, "card": card})


def test_your_own_lace_machine_is_drawn_and_turned_by_hand():
    """The page asks for it by its gears and card, as for a catalogued one."""
    name = "lace:6:101010 010101"
    shape = machine_geometry(name)
    assert len(shape["gears"]) == 6 and len(shape["loading"]) == 6
    assert machine_turned(name, shape["loading"], 2)["time"] == 2
