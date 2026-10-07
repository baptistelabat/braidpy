# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tightening a braid as a window on an endless one, rather than a held piece."""

import numpy as np
import pytest

from braidpy.take_off import (
    Periodic,
    _loop_settler,
    _tied_ends,
    braid_word_trajectories,
    lay_yarns,
    tighten_yarns,
)
from tests.test_take_off import _free_reduce, _word_of_yarns

WORD = [1, -2] * 3  # permutes the strands back to themselves over the window
DIAMETER = 0.4


def laid():
    return lay_yarns(braid_word_trajectories(WORD), yarn_diameter=DIAMETER)


# ── the wrap itself ──────────────────────────────────────────────────────────


def test_a_wrap_must_be_a_permutation():
    Periodic((0, 1, 2))
    Periodic((1, 2, 0))
    with pytest.raises(ValueError, match="permutation"):
        Periodic((0, 0, 1))
    with pytest.raises(ValueError, match="permutation"):
        Periodic((0, 1, 3))


def test_the_wrap_makes_one_loop_per_cycle_of_the_permutation():
    """Yarns that follow one another round the wrap share a loop."""
    turning = Periodic((1, 2, 3, 0)).loops(4, 3)
    assert len(turning) == 1
    assert sorted(turning[0]) == list(range(12))

    standing = Periodic((0, 1, 2, 3)).loops(4, 3)
    assert len(standing) == 4
    assert [list(loop) for loop in standing] == [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [9, 10, 11],
    ]


def test_a_repeated_last_level_is_left_out_of_the_loop():
    """It is its first level over again, not a sample of its own."""
    loose = Periodic((0, 1)).loops(2, 4, tied=False)
    tied = Periodic((0, 1)).loops(2, 4, tied=True)
    assert [len(loop) for loop in loose] == [4, 4]
    assert [len(loop) for loop in tied] == [3, 3]
    assert [list(loop) for loop in tied] == [[0, 1, 2], [4, 5, 6]]


def test_the_repeat_is_recognised():
    paths = laid()
    formed = paths.formed()
    wrap = Periodic(tuple(range(len(paths.points))))
    assert _tied_ends(formed, wrap), "a whole window ends where it began"

    moved = formed.copy()
    moved[0, -1, 0] += 1.0
    assert not _tied_ends(moved, wrap)


# ── the solver round a loop ──────────────────────────────────────────────────


@pytest.mark.parametrize("length", [5, 6, 12, 33])
def test_the_loop_solver_is_the_inverse_it_stands_for(length):
    """Round a loop the matrix is circulant, so a transform does it exactly."""
    weight = 1.5
    lap = np.zeros((length, length))
    for i in range(length):
        lap[i, (i - 1) % length] = -1.0
        lap[i, i] = 2.0
        lap[i, (i + 1) % length] = -1.0
    dense = np.linalg.inv(np.eye(length) + weight * lap)

    values = np.random.default_rng(0).normal(size=(length, 2))
    assert _loop_settler(length, weight)(values) == pytest.approx(dense @ values)


# ── tightening with it ───────────────────────────────────────────────────────


def test_a_wrapped_braid_tightens_without_overlapping():
    paths = laid()
    wrap = Periodic(tuple(range(len(paths.points))))
    tight, history = tighten_yarns(paths, DIAMETER, iterations=120, periodic=wrap)
    assert tight.closest_approach() >= DIAMETER * (1 - 2e-3)
    assert history["length"][-1] < history["length"][0]


def test_a_wrapped_braid_is_still_the_braid_it_was():
    paths = laid()
    wrap = Periodic(tuple(range(len(paths.points))))
    tight, _ = tighten_yarns(paths, DIAMETER, iterations=120, periodic=wrap)
    assert _free_reduce(_word_of_yarns(tight)) == _free_reduce(WORD)


def test_the_repeated_level_keeps_up_with_the_one_it_repeats():
    paths = laid()
    order = tuple(range(len(paths.points)))
    tight, _ = tighten_yarns(paths, DIAMETER, iterations=80, periodic=Periodic(order))
    formed = tight.formed()[:, :, :2]
    assert formed[:, -1] == pytest.approx(formed[list(order), 0], abs=1e-12)


def test_letting_the_ends_go_lets_the_braid_pull_in_further():
    """Which is the point: held ends are a boundary the real braid has not."""
    paths = laid()
    wrap = Periodic(tuple(range(len(paths.points))))
    held, _ = tighten_yarns(paths, DIAMETER, iterations=150)
    free, _ = tighten_yarns(paths, DIAMETER, iterations=150, periodic=wrap)

    def spread(result):
        formed = result.formed()[:, :, :2]
        widths = [
            float(np.max(np.linalg.norm(pts[:, None] - pts[None], axis=-1)))
            for pts in formed.transpose(1, 0, 2)
        ]
        return max(widths) - min(widths)

    # the held braid is wider at its middle than at its pinned ends; the
    # wrapped one has no ends to be pinned, so it varies less along its length
    assert spread(free) < spread(held)


def test_holding_the_ends_leaves_them_where_they_were_and_wrapping_does_not():
    paths = laid()
    start = paths.formed()[:, :, :2].copy()
    wrap = Periodic(tuple(range(len(paths.points))))
    held, _ = tighten_yarns(paths, DIAMETER, iterations=100)
    free, _ = tighten_yarns(paths, DIAMETER, iterations=100, periodic=wrap)

    assert held.formed()[:, 0, :2] == pytest.approx(start[:, 0], abs=1e-9)
    assert held.formed()[:, -1, :2] == pytest.approx(start[:, -1], abs=1e-9)
    assert np.max(np.abs(free.formed()[:, 0, :2] - start[:, 0])) > 1e-3


def test_a_wrap_of_the_wrong_size_says_so():
    paths = laid()
    with pytest.raises(ValueError, match="partner covers"):
        tighten_yarns(paths, DIAMETER, iterations=1, periodic=Periodic((0, 1)))
