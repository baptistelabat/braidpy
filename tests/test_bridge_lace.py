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
        on = [g for g in range(card.n_gears) if ccw[g] or cw[g]]
        assert all((b - a) % card.n_gears > 1 for a, b in zip(on, on[1:]))
        assert all(g % 2 == 0 for g in range(card.n_gears) if ccw[g])
        assert all(g % 2 == 1 for g in range(card.n_gears) if cw[g])
    card.machine()  # the machine itself refuses a card that breaks these


def test_crossings_already_signed_as_their_gears_need_no_moving():
    """The Dutch braid alternates as the gears do: a step per crossing."""
    dutch = Braid((-1, 2) * 6, 3)
    assert len(lace_card(dutch).steps) == 12


def test_the_plait_moves_its_strands_along_and_back():
    """σ₁ is positive but gear 1 turns clockwise: the strands move along a
    notch, three half turns, then every crossing is its gear's; and they
    move back at the end, three more — one beside the last crossing — so
    the card can run again."""
    plait = Braid((1, -2) * 6, 3)
    assert len(lace_card(plait).steps) == 12 + 3 + 3 - 1


def test_a_card_run_round_again_makes_the_braid_again():
    """The strands end in the notches they began in — each in another's,
    as the braid takes them — so the card can run round again."""
    for braid in (Braid((1, -2), 3), Braid((1, 2, -3), 4), Braid((-1, 3, 2), 4)):
        card = lace_card(braid)
        filled = [k is not None for k in card.bobbins]
        assert [k is not None for k in card.program.ends()] == filled
        twice = lace_card(Braid(tuple(braid.generators) * 2, braid.n_strands))
        assert lace_braid(twice) == Braid(tuple(braid.generators) * 2, braid.n_strands)


def test_the_card_as_punched():
    card = lace_card(Braid((-1, 2), 3))
    assert card.steps == (
        ((False,) * 4, (False, True, False, False)),
        ((False, False, True, False), (False,) * 4),
    )
    assert card.text().splitlines() == [
        "     A B C D",
        "0 ↺  ○ ○ ○ ○",
        "  ↻   ○ ● ○ ○",
        "1 ↺  ○ ○ ● ○",
        "  ↻   ○ ○ ○ ○",
    ]
    assert card.threading() == {
        0: ("A", 0),
        1: ("B", 0),
        2: ("C", 0),
    }
    # Named as the machine names its contacts, without building it.
    contacts = {conn.name for conn in card.machine().connections}
    assert card.notches() == ["A-B", "B-C", "C-D"]
    assert set(card.notches()) <= contacts


@pytest.mark.parametrize("gears", [3, 5, 6])
def test_a_ring_that_cannot_hold_the_strands_is_refused(gears):
    """Odd, or too few for six strands and a spare notch."""
    with pytest.raises(ValueError, match="notch to spare"):
        lace_card(Braid((1, 2, 3, 4, 5), 6), n_gears=gears)
