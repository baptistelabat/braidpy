# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids on a ring of slots, and the shape a laid rope takes."""

import pytest

from braidpy.annulus_braid import (
    rope,
    wrap_crossing,
    tubular_paths,
    turn,
)


# ── The word ──────────────────────────────────────────────────────────────────


def test_a_turn_is_not_a_crossing():
    """Nobody passes anybody when the whole ring goes round together.

    This is what separates a rope from a braid, and it is the reason a rope
    has a shape anyone can write down.
    """
    paths = tubular_paths(rope(3), 3)
    assert all(all(sign == 0 for sign in path.signs) for path in paths)
    assert all(path.turns == 1.0 for path in paths)
    # The unwrapped slot number counts on past the last slot, not resetting.
    assert paths[0].slots == (0, 1, 2, 3)


def test_a_crossing_sends_one_strand_outside_and_one_in():
    assert sorted(path.signs[0] for path in tubular_paths([1], 3)) == [-1, 0, 1]
    assert tubular_paths([-1], 3)[0].signs[0] == -tubular_paths([1], 3)[0].signs[0]


def test_the_wrapping_crossing_carries_a_strand_round():
    """Index N joins the last slot to slot zero, which a line cannot do."""
    paths = tubular_paths([wrap_crossing(3)], 3)
    assert paths[0].slots == (0, -1), "slot zero steps back a lap"
    assert paths[2].slots == (2, 3), "the last carries on round"


def test_a_tubular_braid_sends_its_strands_both_ways():
    paths = tubular_paths([1, 3, wrap_crossing(4), 2], 4)
    assert sorted(path.turns for path in paths) == [-0.5, -0.5, 0.5, 0.5]


def test_a_move_the_ring_does_not_have_is_refused():
    with pytest.raises(ValueError, match="not one of this ring"):
        tubular_paths([9], 3)


def test_turn_and_crossing_indices_do_not_collide():
    assert turn(3) != wrap_crossing(3)
    assert tubular_paths([turn(3)], 3)[0].signs == (0,)
    assert tubular_paths([wrap_crossing(3)], 3)[0].signs != (0,)


# ── The one shape that is closed-form and physical ────────────────────────────


# ── A braided tube, after the geometric model ─────────────────────────────────
