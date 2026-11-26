# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as a punchcard for the Jacquard lace machine:
braidpy.making.lace, checked by running the machine."""

import itertools

import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.making.lace import _gear_sign, lace_braid, lace_card


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
        assert all((b - a) % card.n_gears > 1 for a, b in itertools.pairwise(on))
        assert all(g % 2 == 0 for g in range(card.n_gears) if ccw[g])
        assert all(g % 2 == 1 for g in range(card.n_gears) if cw[g])
    card.machine()  # the machine itself refuses a card that breaks these


def test_crossings_already_signed_as_their_gears_need_no_moving():
    """The Dutch braid alternates as the gears do: a step per crossing."""
    dutch = Braid((-1, 2) * 6, 3)
    assert len(lace_card(dutch).steps) == 12


def test_the_plait_begun_a_notch_along_needs_no_moving():
    """σ₁ is positive, but gear 1 turns clockwise: begun from notch 0, the
    strands must move.  Begun a notch along, every crossing is its gear's,
    and the plait takes a step a crossing on four gears."""
    plait = Braid((1, -2) * 6, 3)
    card = lace_card(plait, n_gears=4)
    assert len(card.steps) == 12
    assert card.notches() == ["B-C", "C-D", "D-A"]
    assert lace_braid(card) == plait


def test_the_search_finds_the_fewest_steps_of_small_braids():
    """The fewest steps there are, found by trying every turn of every gear
    (scratch work): the square sinnet of 4 on six gears in 8, though it has
    6 crossings, as two of them must wait for a strand to move; the
    asymmetric flat braid of 4 in 4."""
    from braidpy.braid_catalog import CATALOGUE
    from braidpy.pure_braid import repeating_unit

    for name, gears, fewest in (("square4", 6, 8), ("asymmetric_flat4", 6, 4)):
        made = CATALOGUE[name].make()
        unit = Braid(tuple(repeating_unit(made.generators)), made.n_strands)
        assert len(lace_card(unit, n_gears=gears).steps) == fewest, name


def test_strands_spread_out_move_only_in_pairs():
    """With a notch spare beside each strand, a crossing whose sign is not
    its gear's moves its two strands only: the book's #3047, 94 crossings
    of 19 strands, in a few steps a crossing rather than twenty."""
    from braidpy.solid_sinnets_catalog import abok_3047

    braid = abok_3047.braid(1)
    card = lace_card(braid)
    assert len(card.steps) < 2 * len(braid.generators)
    assert lace_braid(card) == braid


def test_the_card_of_fewest_steps_is_kept():
    """Of the gears tried, the card of fewest steps, packed or spread."""
    braid = Braid((1, -2, 3, -1, 2) * 2, 4)
    best = lace_card(braid)
    for gears in (6, 8):
        assert len(best.steps) <= len(lace_card(braid, n_gears=gears).steps)


def test_a_braid_of_no_crossing_is_a_step_turning_no_gear():
    """A card has a step: for no crossing, one turning no gear."""
    card = lace_card(Braid((), 4))
    assert len(card.steps) == 1
    assert not any(any(line) for line in card.steps[0])
    assert lace_braid(card) == Braid((), 4)


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


def test_a_card_run_on_its_ring_is_the_braid_the_machine_reads():
    """Each gear's turn its two notches swapping bobbins, the crossing the
    sign of its turn: the braid the machine itself makes, word for word,
    for every card of the catalogue and for cards made from braid words."""
    import random

    from braidpy.machine_catalog import LACE
    from braidpy.making.lace import card_program, ring_braid

    for entry in LACE.values():
        ring = entry.make()
        program = card_program(ring.n_gears, ring.steps, ring.threaded)
        assert program.braid().generators == ring_braid(ring.machine()).generators
    rng = random.Random(0)
    for _ in range(30):
        n = rng.randint(2, 6)
        word = [rng.choice([-1, 1]) * rng.randint(1, n - 1) for _ in range(8)]
        card = lace_card(Braid(word, n))
        program = card_program(card.n_gears, card.steps, card.threaded())
        assert program.braid() == lace_braid(card)


def test_a_gear_turned_the_wrong_way_is_refused():
    from braidpy.making.lace import card_program

    with pytest.raises(ValueError, match="cannot turn anticlockwise"):
        card_program(4, [((False, True, False, False), (False,) * 4)])


def test_no_card_takes_fewer_steps_than_its_floor():
    """The floor is no more than the steps of any card found, and the
    fewest there are for the square sinnet of 4 (8, by trying every turn
    of every gear): two of its crossings wait for a strand to move."""
    from braidpy.braid_catalog import CATALOGUE
    from braidpy.making.lace import step_floor
    from braidpy.pure_braid import repeating_unit

    for name, entry in CATALOGUE.items():
        made = entry.make()
        unit = Braid(tuple(repeating_unit(made.generators)), made.n_strands)
        word = [int(g) for g in unit.generators]
        assert step_floor(word, unit.n_strands) <= len(lace_card(unit).steps), name
    assert step_floor([-1, -2, -2, 3, 2, 2], 4) == 8


def test_the_floor_a_repeat_does_not_depend_on_where_the_word_is_cut():
    from braidpy.making.lace import repeat_floor, step_floor
    from braidpy.solid_sinnets_catalog import abok_3059

    word = [int(g) for g in abok_3059.braid(1).generators]
    n = abok_3059.n_strands
    floors = {repeat_floor(word[k:] + word[:k], n) for k in range(len(word))}
    assert len(floors) == 1
    assert len({step_floor(word[k:] + word[:k], n) for k in range(len(word))}) > 1


def test_a_card_conjugate_is_the_same_braid_once_repeated():
    """Read from elsewhere and rewritten by the braid relations: a
    conjugate, exactly, on braids small enough to tell; of a floor no
    higher; the same each time."""
    import random

    from braidpy.conjugacy import are_conjugate
    from braidpy.making.lace import card_conjugate, repeat_floor

    rng = random.Random(0)
    for _ in range(10):
        n = rng.randint(3, 5)
        braid = Braid(
            [rng.choice((-1, 1)) * rng.randint(1, n - 1) for _ in range(10)], n
        )
        found = card_conjugate(braid, tries=300)
        assert are_conjugate(found, braid)
        assert repeat_floor(list(found.generators), n) <= repeat_floor(
            list(braid.generators), n
        )
        assert card_conjugate(braid, tries=300).generators == found.generators


def test_the_book_s_sinnets_rewritten_take_far_fewer_steps():
    """#3047, a cascade of one strand crossing many after another: a
    conjugate of it, the same braid by its topology, takes a card far
    shorter."""
    from braidpy.making.lace import card_conjugate
    from braidpy.ring_program import same_braid
    from braidpy.solid_sinnets_catalog import abok_3047

    braid = abok_3047.braid(1)
    found = card_conjugate(braid)
    assert same_braid(found, braid)
    assert len(lace_card(found).steps) < 0.7 * len(lace_card(braid).steps)


def test_a_card_as_typed_is_read_back():
    """A card written as Braid Studio takes it is read back step for step,
    however its steps are laid out on lines."""
    from braidpy.making.lace import card_digits, read_card

    card = lace_card(Braid((1, -2, 3, -1), 4))
    typed = card_digits(card.steps)
    assert read_card(typed, card.n_gears) == [tuple(map(tuple, s)) for s in card.steps]
    assert read_card(typed.replace("\n", " "), card.n_gears) == read_card(
        typed, card.n_gears
    )
    with pytest.raises(ValueError, match="two groups"):
        read_card("0101", 4)


def test_gears_are_named_as_spreadsheet_columns():
    from braidpy.making.lace import gear_name, gear_number

    assert [gear_name(g) for g in (0, 25, 26, 51, 52, 71)] == [
        "A",
        "Z",
        "AA",
        "AZ",
        "BA",
        "BT",
    ]
    assert all(gear_number(gear_name(g)) == g for g in range(200))
    assert gear_number("ab") == 27


def test_a_card_is_written_by_the_gears_each_step_turns():
    """Far shorter than its digits, and read back the same; a step turning
    no gear is -."""
    from braidpy.making.lace import card_digits, card_names, read_card

    card = lace_card(Braid((1, -2, 3, -1) * 3, 4), n_gears=8)
    names = card_names(card.steps)
    assert read_card(names, 8) == [tuple(map(tuple, s)) for s in card.steps]
    assert len(names) < len(card_digits(card.steps)) / 2
    assert card_names([((False,) * 4, (False,) * 4)]) == "-"
    assert read_card("- / A", 4)[0] == ((False,) * 4, (False,) * 4)
    assert card.spec()["card"] == names


def test_a_punchcard_past_26_gears_keeps_its_columns():
    """Gears AA and on: every column as wide as the longest name, each punch
    under its gear's name."""
    from braidpy.making.lace import punchcard_text

    turning = tuple(g == 27 for g in range(30))
    text = punchcard_text([(turning, (False,) * 30)])
    header, anticlockwise = text.splitlines()[:2]
    assert header.index("AB") == anticlockwise.index("●")
