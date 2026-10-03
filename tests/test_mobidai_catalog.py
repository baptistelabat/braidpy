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
    braid = CATALOGUE[name]
    disk = Mobidai(braid.to_config())
    disk.all_steps()
    assert len(disk.generators) > 0, "a braid with no crossings is not a braid"


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_every_strand_keeps_its_slot_to_itself(name):
    """No two strands start in the same place."""
    braid = CATALOGUE[name]
    slots = [slot for slot, _ in braid.initial_slots]
    assert len(set(slots)) == len(slots)
    assert braid.n_strands == len(braid.initial_slots)


def test_all_four_braids_from_the_book_are_reachable():
    """They were not: the module rebound the same two names four times.

    Only the last braid survived import, so three of the four could not be
    used at all.  This is the test that would have caught it.
    """
    assert len(CATALOGUE) == 4
    assert sorted(braid.n_strands for braid in CATALOGUE.values()) == [7, 8, 12, 16]


def test_the_braid_that_needs_a_turn_between_cycles_records_it():
    """One braid is a cycle of moves *plus* a rotation, and says so."""
    seven = next(b for b in CATALOGUE.values() if b.n_strands == 7)
    assert seven.n_slots == 8
    assert seven.n_shift_after_cycle == -3


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_a_catalogued_braid_gives_a_word_braidpy_understands(name):
    from braidpy.braid import Braid

    braid = CATALOGUE[name]
    disk = Mobidai(braid.to_config())
    disk.all_steps()
    word = disk.generators
    assert all(1 <= abs(generator) <= braid.n_strands - 1 for generator in word)
    assert Braid(tuple(word), n_strands=braid.n_strands).format()
