# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids transcribed from the Delage-Calvet book.

Transcribed data is data that can be mistyped, and a slot number out by one
shows up as a braid that cannot be made.  Running each catalogued braid is
therefore the check that matters: it exercises every slot and every move.
"""

import pytest

from braidpy.mobidai import Mobidai
from braidpy.mobidai_catalog import CATALOGUE


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_every_catalogued_braid_can_actually_be_made(name):
    """The disk accepts the threading and every move in the cycle.

    A mistyped slot shows up here as a collision or an invalid slot, which is
    the whole reason for running them rather than only storing them.
    """
    braid = CATALOGUE[name].make()
    disk = Mobidai(braid.to_config())
    disk.all_steps()
    assert len(disk.generators) > 0, "a braid with no crossings is not a braid"


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_every_strand_keeps_its_slot_to_itself(name):
    """No two strands start in the same place."""
    braid = CATALOGUE[name].make()
    slots = [slot for slot, _ in braid.initial_slots]
    assert len(set(slots)) == len(slots)
    assert braid.n_strands == len(braid.initial_slots)


def test_all_four_braids_from_the_book_are_reachable():
    """They were not: the module rebound the same two names four times.

    Only the last braid survived import, so three of the four could not be
    used at all.  This is the test that would have caught it.
    """
    book = [e.make() for e in CATALOGUE.values() if "Delage-Calvet" in e.reference]
    assert sorted(braid.n_strands for braid in book) == [7, 8, 12, 16]


def test_the_braid_that_needs_a_turn_between_cycles_records_it():
    """One braid is a cycle of moves *plus* a rotation, and says so."""
    seven = next(b for b in (e.make() for e in CATALOGUE.values()) if b.n_strands == 7)
    assert seven.n_slots == 8
    assert seven.n_shift_after_cycle == -3


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_a_catalogued_braid_gives_a_word_braidpy_understands(name):
    from braidpy.braid import Braid

    braid = CATALOGUE[name].make()
    disk = Mobidai(braid.to_config())
    disk.all_steps()
    word = disk.generators
    assert all(1 <= abs(generator) <= braid.n_strands - 1 for generator in word)
    assert Braid(tuple(word), n_strands=braid.n_strands).format()


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_every_cycle_is_made_from_where_the_last_left_off(name):
    """Cycle after cycle, every move finds a strand to move.

    Most of these braids leave the strands a slot round from where they
    began, and the braider makes the next cycle from there.  Repeating the
    moves from the same slots instead finds them empty by the second cycle,
    and the braid stops being made.
    """
    braid = CATALOGUE[name].make()
    disk = Mobidai(braid.to_config())
    disk.all_steps()
    per_cycle = len(disk.braid_word)
    for _ in range(5):
        disk.all_steps()
    assert len(disk.braid_word) == 6 * per_cycle


# The braids Richard Buenger shared in the Kumihimo group, as the Braid Studio
# links in issues #111 to #114 give them: slots, moves and colours.
SHARED = {
    "HIRA_NAIKI": (
        "31 2 4 5 8 9 12 13 16 17 20 21 24 25 28 29",
        (
            "17>32, 16>1, 2>16, 31>17, 1>2, 32>31, 28>3, 12>19, 4>7, 20>23, 3>4,"
            " 19>20, 8>12, 24>28, 7>8, 23>24, 29>26, 13>10, 25>22, 26>25, 9>6,"
            " 10>9, 5>29, 6>5, 21>13, 22>21"
        ),
        (
            "#e41a1c,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,#e41a1c,"
            "#e41a1c,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,#e41a1c"
        ),
    ),
    "EDO_YATSU": (
        "32 1 17 16 25 24 8 9",
        (
            "32>7, 8>15, 16>23, 24>32, 7>8, 15>16, 23>24, 1>26, 25>18, 17>10,"
            " 9>1, 26>25, 18>17, 10>9"
        ),
        None,
    ),
    "NAIKI": (
        "32 1 4 5 12 13 17 16 20 21 25 24 28 29 8 9",
        (
            "32>3, 4>7, 8>11, 12>15, 16>19, 20>23, 24>27, 28>32, 3>4, 7>8, 11>12,"
            " 15>16, 19>20, 23>24, 27>28, 1>30, 29>26, 25>22, 21>18, 17>14, 13>10,"
            " 9>6, 5>1, 30>29, 26>25, 22>21, 18>17, 14>13, 10>9, 6>5"
        ),
        None,
    ),
    "UNERI_MARU_GENJI": (
        "31 2 3 5 6 8 9 11 12 14 15 18 19 21 22 24 25 27 28 30",
        (
            "19>32, 14>1, 3>16, 30>17, 22>4, 6>20, 21>22, 20>21, 5>6, 4>5, 25>7,"
            " 9>23, 24>25, 23>24, 8>9, 7>8, 28>10, 12>26, 27>28, 26>27, 11>12,"
            " 10>11, 15>14, 16>15, 18>19, 17>18, 2>3, 1>2, 31>30, 32>31"
        ),
        (
            "#66c2a5,#4daf4a,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,#ffffff,"
            "#377eb8,#555555,#555555,#377eb8,#ffffff,#ffffff,#ffffff,#ffffff,"
            "#ffffff,#ffffff,#4daf4a,#66c2a5"
        ),
    ),
}


@pytest.mark.parametrize("name", sorted(SHARED))
def test_a_shared_braid_is_the_braid_its_link_makes(name):
    """Picked from the catalogue, each braid is the braid made from its link:
    the same strands, laid the same way, in the same colours."""
    from braidpy.web import build

    slots, moves, colours = SHARED[name]
    link = {"source": "mobidai", "name": "custom", "slots": slots, "moves": moves}
    link |= {"n_slots": 32, "shift": 0, "cycles": 2}
    if colours:
        link["colours"] = colours
    shared = build(link, tighten=False)
    catalogued = build({"source": "mobidai", "name": name, "cycles": 2}, tighten=False)
    assert [s["colour"] for s in catalogued["strands"]] == [
        s["colour"] for s in shared["strands"]
    ]
    assert [s["points"] for s in catalogued["strands"]] == [
        s["points"] for s in shared["strands"]
    ]


def test_edo_yatsu_is_ashleys_8_strand_square():
    """Edo yatsu, made on a kumihimo disk, is ABOK #3070 made on Ashley's
    stand: nothing braidpy measures tells them apart, so each is listed as a
    way of making the other."""
    from braidpy.ring_program import same_braid
    from braidpy.topology_catalog import braid_of
    from braidpy.web import build

    def braid(spec):
        return braid_of(build({**spec, "cycles": 1}, tighten=False)["info"])

    edo = braid({"source": "mobidai", "name": "EDO_YATSU"})
    ashley = braid({"source": "sinnet", "name": "abok_3070"})
    assert same_braid(edo, ashley)
