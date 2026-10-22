# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a punchcard for the Jacquard lace machine:
braidpy.bridges.lace, checked by running the machine."""

import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.bridges.lace import _gear_sign, lace_braid, lace_card


def _words():
    for example in word_examples():
        if example.get("layout") == "ring":
            continue
        word = tuple(int(g) for g in example["word"].split()) * example["repeat"]
        yield example["title"], Braid(word, example["n_strands"])


def test_every_catalogue_word_is_made_on_the_lace_machine():
    """The card run on the machine makes the very braid."""
    for title, braid in _words():
        card = lace_card(braid)
        assert lace_braid(card) == braid, title


def test_each_crossing_is_made_by_a_gear_turning_its_way():
    for title, braid in _words():
        card = lace_card(braid)
        for row in card.program.rows:
            for swap in row:
                gear = (swap.place + 1) % card.n_gears
                assert swap.sign == _gear_sign(gear), title


def test_a_step_turns_no_two_touching_gears_each_its_own_way():
    card = lace_card(Braid((1, 2, -3, 1, 2) * 3, 4))
    for ccw, cw in card.steps:
        on = [g for g in range(card.n_gears) if "1" in (ccw[g], cw[g])]
        assert all((b - a) % card.n_gears > 1 for a, b in zip(on, on[1:]))
        assert all(g % 2 == 0 for g in range(card.n_gears) if ccw[g] == "1")
        assert all(g % 2 == 1 for g in range(card.n_gears) if cw[g] == "1")
    card.machine()  # the machine itself refuses a card that breaks these


def test_crossings_already_signed_as_their_gears_need_no_moving():
    """The Dutch braid alternates as the gears do: a step per crossing."""
    dutch = Braid((-1, 2) * 6, 3)
    assert len(lace_card(dutch).steps) == 12


def test_the_plait_moves_its_strands_along_once():
    """σ₁ is positive but gear 1 turns clockwise: the strands move along a
    notch, three half turns, and then every crossing is its gear's."""
    plait = Braid((1, -2) * 6, 3)
    assert len(lace_card(plait).steps) == 12 + 3


def test_the_card_as_punched():
    card = lace_card(Braid((-1, 2), 3))
    assert card.text().splitlines() == ["0000 0100", "0010 0000"]
    assert card.threading() == {
        0: ("A", 0),
        1: ("B", 0),
        2: ("C", 0),
    }


@pytest.mark.parametrize("gears", [3, 5, 6])
def test_a_ring_that_cannot_hold_the_strands_is_refused(gears):
    """Odd, or too few for six strands and a spare notch."""
    with pytest.raises(ValueError, match="notch to spare"):
        lace_card(Braid((1, 2, 3, 4, 5), 6), n_gears=gears)
