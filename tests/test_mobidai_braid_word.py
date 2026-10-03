# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braid word a Mobidai makes, which until now was taken on trust.

:class:`~braidpy.mobidai.BraidTracker` accumulates Artin generators as strands
are moved about the disk, and nothing checked the result.  The check that
matters is the same one the Kumihimo disk has to pass: the word must permute
the strands exactly the way the disk did.  A word that does not is not the
word of that braid, however reasonable it reads.
"""

import pytest

from braidpy.mobidai import Mobidai, MobidaiConfig, Move, Strand


def disk(moves, strands, n_slots=8, **config):
    """Run a Mobidai to completion and hand it back."""
    machine = Mobidai(
        MobidaiConfig(
            n_slots=n_slots,
            strands=strands,
            moves=moves,
            n_shift_after_cycle=0,
            **config,
        )
    )
    machine.all_steps()
    return machine


def permutation_of(generators, count):
    """Where a braid word sends each position, applied left to right."""
    order = list(range(count))
    for generator in generators:
        low = abs(generator) - 1
        order[low], order[low + 1] = order[low + 1], order[low]
    return order


# ── The invariant ─────────────────────────────────────────────────────────────


def test_the_word_permutes_the_strands_the_way_the_disk_did():
    """One strand carried past three others ends up behind all of them."""
    machine = disk(
        [Move(1, 5)],
        [Strand("a", 1), Strand("b", 2), Strand("c", 3), Strand("d", 4)],
    )
    assert machine.generators == [1, 2, 3]
    assert permutation_of(machine.generators, 4) == machine.braid_tracker.linear_order


@pytest.mark.parametrize(
    "moves",
    [
        [Move(1, 5)],
        [Move(1, 5), Move(2, 6)],
        [Move(4, 8)],
        [Move(2, 7), Move(7, 2)],
        [Move(1, 6), Move(4, 1)],
    ],
)
def test_the_word_and_the_tracker_agree_whatever_the_moves(moves):
    """The tracker updates its order as it emits; the two must not drift."""
    strands = [Strand(f"s{slot}", slot) for slot in (1, 2, 3, 4)]
    machine = disk(moves, strands)
    assert permutation_of(machine.generators, 4) == machine.braid_tracker.linear_order


def test_moving_into_empty_slots_crosses_nobody():
    """No strand passed, so no generator — an empty word, not a wrong one."""
    machine = disk([Move(1, 5)], [Strand("lonely", 1)])
    assert machine.braid_word == []
    assert machine.generators == []


# ── Which way round decides the sign ──────────────────────────────────────────


def test_going_one_way_round_is_the_inverse_of_going_the_other():
    """The same pair of strands, crossed in opposite directions.

    Clockwise the mover passes over, anticlockwise it passes under, so the
    two words are inverses of one another.
    """
    clockwise = disk([Move(1, 3)], [Strand("x", 1), Strand("y", 2)])
    anticlockwise = disk([Move(1, 7)], [Strand("x", 1), Strand("y", 8)])
    assert clockwise.generators == [1]
    assert anticlockwise.generators == [-1]


def test_a_longer_reach_crosses_everyone_on_the_way():
    """Two strands in the path means two generators, in the order met."""
    machine = disk([Move(1, 4)], [Strand("x", 1), Strand("y", 2), Strand("z", 3)])
    assert machine.generators == [1, 2]


# ── The word is usable by the rest of braidpy ─────────────────────────────────


def test_the_generators_are_the_readable_word_in_integer_form():
    """`braid_word` stays readable; `generators` is what Braid can take."""
    machine = disk(
        [Move(1, 5)],
        [Strand("a", 1), Strand("b", 2), Strand("c", 3), Strand("d", 4)],
    )
    assert machine.braid_word == ["s1 s2 s3"]
    assert machine.generators == [1, 2, 3]
    assert all(isinstance(generator, int) for generator in machine.generators)


def test_the_word_a_disk_makes_is_a_braid_braidpy_understands():
    from braidpy.braid import Braid

    machine = disk(
        [Move(1, 5)],
        [Strand("a", 1), Strand("b", 2), Strand("c", 3), Strand("d", 4)],
    )
    braid = Braid(tuple(machine.generators), n_strands=4)
    assert braid.format()
