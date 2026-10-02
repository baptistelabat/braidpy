# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What a braid word does to the order of the strands."""

from braidpy.braid import Braid
from braidpy.pure_braid import closing_repeats, is_pure, permutation

FLAT = Braid((1, -2), n_strands=3)


def test_slots_are_exchanged_by_position_not_by_strand():
    """A generator names two slots, and swaps whoever is standing in them."""
    history = Braid((1, 1), n_strands=3).slot_history()
    assert history[0] == [0, 1, 2]
    assert history[1] == [1, 0, 2]  # the first two strands have traded slots
    assert history[2] == [0, 1, 2]  # and traded back


def test_a_neutral_generator_moves_nobody():
    assert Braid((0, 0), n_strands=2).slot_history() == [[0, 1], [0, 1], [0, 1]]


def test_the_flat_braid_is_pure_after_three_crossings_of_each_kind():
    assert not is_pure(FLAT)
    assert permutation(FLAT) == [2, 0, 1]
    assert closing_repeats(FLAT) == 3

    closed = Braid((1, -2) * 3, n_strands=3)
    assert is_pure(closed)
    assert permutation(closed) == [0, 1, 2]
    assert closing_repeats(closed) == 1


def test_a_single_twist_closes_after_two():
    assert closing_repeats(Braid((1,), n_strands=2)) == 2
    assert is_pure(Braid((1, 1), n_strands=2))
