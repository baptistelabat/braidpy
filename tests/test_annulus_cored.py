# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A ring braid round its core: annulus_braid.cored_word, turns_last."""

import random

import pytest

from braidpy import Braid
from braidpy.annulus_braid import cored_word, turn, turns_last, wrap_crossing
from braidpy.braid_catalogue import garside_half_twist_braid


@pytest.mark.parametrize("n", [2, 3, 5])
def test_a_turn_n_times_is_a_full_twist_round_the_core(n):
    """Every strand once round the core: the whole cord, core and all,
    twisted once."""
    half = list(garside_half_twist_braid(n + 1).generators)
    assert Braid(tuple(cored_word([turn(n)] * n, n)), n + 1) == Braid(
        tuple(half * 2), n + 1
    )


@pytest.mark.parametrize("n", [3, 5])
def test_a_turn_renumbers_the_crossings_after_it(n):
    """A turn, crossing i, the turn undone: crossing i - 1, read round the
    ring, crossing 1 becoming the wrapping one."""
    for i in range(1, n + 1):
        before = (i - 2) % n + 1
        assert Braid(tuple(cored_word([turn(n), i, -turn(n)], n)), n + 1) == Braid(
            tuple(cored_word([before], n)), n + 1
        )
    assert before == n - 1 and wrap_crossing(n) == n


def test_turns_moved_to_the_end_are_the_same_braid_round_the_core():
    rng = random.Random(0)
    for _ in range(80):
        n = rng.randint(2, 6)
        moves = [
            rng.choice((-1, 1)) * rng.randint(1, n + 1)
            for _ in range(rng.randint(1, 12))
        ]
        last = turns_last(moves, n)
        turns = [m for m in last if abs(m) == n + 1]
        assert last[len(last) - len(turns) :] == turns
        assert len({m > 0 for m in turns}) <= 1
        assert Braid(tuple(cored_word(last, n)), n + 1) == Braid(
            tuple(cored_word(moves, n)), n + 1
        )
