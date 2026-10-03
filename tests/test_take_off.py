# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Laying, drawing in and tightening a braid from any source of strands."""

from types import SimpleNamespace

import numpy as np
import pytest

from braidpy import Braid
from braidpy.parametric_braid import ParametricBraid
from braidpy.symmetric_braid import braid_word
from braidpy.take_off import (
    StrandTrajectories,
    braid_word_trajectories,
    default_take_off,
    disk_trajectories,
    lay_yarns,
    mobidai_steps,
    mobidai_trajectories,
    parametric_trajectories,
    tighten_yarns,
    visualize_yarns,
)


class _Curve:
    """A sampled curve, in the form :func:`braid_word` reads."""

    def __init__(self, s, x, y):
        self.s, self.x, self.y, self.length = s, x, y, float(s[-1])

    def position(self, z):
        return (np.interp(z, self.s, self.x), np.interp(z, self.s, self.y), z)


def _word_of_yarns(paths):
    """The word the laid yarns make, read down from the oldest end."""
    curves = []
    for pts in paths.points.values():
        braid = pts[: paths.formed_count]
        curves.append(_Curve(braid[0, 2] - braid[:, 2], braid[:, 0], braid[:, 1]))
    return braid_word(curves, n_samples=4000)


def _word_of_disk(trajectories, n_slots):
    """The word strands on a disk make, read in slot order, outward as over."""
    curves = []
    for xy in trajectories.xy.values():
        angle = np.unwrap(np.arctan2(xy[:, 0], xy[:, 1]))
        slot = angle * n_slots / (2 * np.pi) + 1
        curves.append(_Curve(trajectories.times, slot, np.hypot(xy[:, 0], xy[:, 1])))
    return braid_word(curves, n_samples=20000)


def _free_reduce(word):
    out = []
    for g in word:
        if out and out[-1] == -g:
            out.pop()
        else:
            out.append(g)
    return out


# ── Trajectories ──────────────────────────────────────────────────────────────


def test_trajectories_are_checked():
    with pytest.raises(ValueError, match="evenly spaced"):
        StrandTrajectories(np.array([0.0, 1.0, 3.0]), {0: np.zeros((3, 2))})
    with pytest.raises(ValueError, match="expected"):
        StrandTrajectories(np.array([0.0, 1.0]), {0: np.zeros((3, 2))})
    with pytest.raises(ValueError, match="two samples"):
        StrandTrajectories(np.array([0.0]), {0: np.zeros((1, 2))})


def test_default_take_off_is_the_mean_speed():
    times = np.linspace(0.0, 2.0, 5)
    moving = np.column_stack([np.linspace(0.0, 4.0, 5), np.zeros(5)])
    still = np.ones((5, 2))
    traj = StrandTrajectories(times, {0: moving, 1: still})
    assert default_take_off(traj) == pytest.approx((4.0 / 2.0) / 2)
    assert traj.centre() == pytest.approx(np.concatenate([moving, still]).mean(0))


def test_parametric_braid_is_read_as_it_is_drawn():
    strands = Braid([1, -2]).to_parametric_strands()
    traj = parametric_trajectories(ParametricBraid(strands), n_samples=11)
    assert traj.times == pytest.approx(np.linspace(0, 1, 11))
    for key, strand in enumerate(strands):
        assert traj.xy[key][4] == pytest.approx(strand.evaluate(0.4)[:2])


# ── A braid word, laid ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word",
    [[1, -2, 1, -2, 1, -2], [1, 1, 2, -1, -1, 2], [1, 2, 3, -1, -2, 2, 1]],
)
def test_braid_word_survives_laying_drawing_in_and_tightening(word):
    """The braid the word names is the braid that comes out, at every stage."""
    traj = braid_word_trajectories(word)
    assert _word_of_yarns(lay_yarns(traj)) == word

    jammed = lay_yarns(traj, yarn_diameter=0.4)
    assert jammed.closest_approach() == pytest.approx(0.4)
    assert _word_of_yarns(jammed) == word

    # Tightening may pull out a crossing that undoes itself, but never changes
    # the braid.
    tight, _ = tighten_yarns(jammed, 0.4, iterations=100)
    assert tight.closest_approach() >= 0.4 * (1 - 2e-3)
    assert _free_reduce(_word_of_yarns(tight)) == _free_reduce(word)


def test_braid_word_layout():
    traj = braid_word_trajectories(Braid([1]), spacing=2.0, lift=0.25)
    xs = sorted(xy[0, 0] for xy in traj.xy.values())
    assert xs == pytest.approx([0.0, 2.0])
    # Half way through the crossing the two are lifted to either side.
    middle = len(traj.times) // 4
    lifts = sorted(xy[middle, 1] for xy in traj.xy.values())
    assert lifts[0] == pytest.approx(-lifts[1])
    assert lifts[1] == pytest.approx(0.5, rel=0.05)


# ── A disk ────────────────────────────────────────────────────────────────────


def test_a_moving_strand_passes_over_on_the_outside():
    # Toward higher slots, over the strand in between: a positive crossing on
    # a clockwise disk, as the mobidai's word has it.
    traj = disk_trajectories({"a": 1, "b": 2}, [{"a": 2}], n_slots=8)
    assert _word_of_disk(traj, 8) == [1]
    radius = np.hypot(*traj.xy["a"].T)
    assert radius.max() == pytest.approx(1.15)
    assert radius[0] == radius[-1] == pytest.approx(1.0)
    # The other way, under it.
    back = disk_trajectories({"a": 3, "b": 2}, [{"a": -2}], n_slots=8)
    assert _word_of_disk(back, 8) == [-1]


def test_turning_the_disk_lifts_nothing():
    traj = disk_trajectories({0: 1, 1: 5}, [{0: 2, 1: 2}], n_slots=8)
    for xy in traj.xy.values():
        assert np.hypot(*xy.T) == pytest.approx(1.0)
    assert _word_of_disk(traj, 8) == []
    # Slot 1 at the top, and clockwise means clockwise seen from above.
    assert traj.xy[0][0] == pytest.approx([0.0, 1.0])
    assert traj.xy[0][-1] == pytest.approx([1.0, 0.0])
    mirrored = disk_trajectories({0: 1, 1: 5}, [{0: 2, 1: 2}], 8, clockwise=False)
    assert mirrored.xy[0][-1] == pytest.approx([-1.0, 0.0])


def test_disk_refuses_impossible_moves():
    with pytest.raises(ValueError, match="one slot"):
        disk_trajectories({0: 1, 1: 3}, [{0: 2}], n_slots=8)
    with pytest.raises(ValueError, match="unknown"):
        disk_trajectories({0: 1}, [{5: 1}], n_slots=8)
    with pytest.raises(ValueError, match="not on a slot"):
        disk_trajectories({0: 9}, [], n_slots=8)
    with pytest.raises(ValueError, match="same slot"):
        disk_trajectories({0: 1, 1: 1}, [], n_slots=8)


def _mobidai_config(moves, positions, n_slots=16, shift=0):
    """Shaped like braidpy.mobidai's MobidaiConfig, which this reads."""
    return SimpleNamespace(
        n_slots=n_slots,
        is_clockwise=True,
        n_shift_after_cycle=shift,
        strands=[SimpleNamespace(position=p, id=-1) for p in positions],
        moves=[
            SimpleNamespace(from_slot=a, to_slot=b, force_direction=f)
            for a, b, f in moves
        ],
    )


def test_mobidai_steps_follow_its_rules():
    config = _mobidai_config(
        [(1, 4, 0), (12, 10, 0), (5, 7, 0), (2, 15, 0), (3, 6, -1)],
        positions=[1, 2, 3, 12],
        shift=1,
    )
    start, steps = mobidai_steps(config, n_cycles=1)
    assert start == {0: 1, 1: 2, 2: 3, 3: 12}
    assert steps == [
        {0: 3},  # the short way, up
        {3: -2},  # the short way, down
        # slot 5 is empty: nothing moves
        {1: -3},  # 2 to 15 is shorter downward, through slot 1
        {2: -13},  # forced the long way round
        {0: 1, 1: 1, 2: 1, 3: 1},  # the disk turns
    ]
    # A Mobidai object is read through its config.
    assert mobidai_steps(SimpleNamespace(config=config))[0] == start


def test_mobidai_is_laid_and_tightened():
    config = _mobidai_config(
        [(1, 5, 0), (9, 13, 0), (6, 2, 0), (14, 10, 0)],
        positions=[1, 3, 6, 9, 11, 14],
        shift=2,
    )
    traj = mobidai_trajectories(config, n_cycles=3)
    assert set(traj.xy) == set(range(6))
    paths = lay_yarns(traj, yarn_diameter=0.15, fell_radius=0.0)
    tight, history = tighten_yarns(paths, 0.15, iterations=40)
    assert history["length"][-1] < history["length"][0]
    assert tight.closest_approach(include_fell=False) >= 0.15 * (1 - 2e-3)

    fig = visualize_yarns(tight)
    names = [t.name for t in fig.data]
    assert "Disk" in names and "Braiding point" in names
    assert sum(1 for n in names if n.startswith("Strand ")) == 6
    assert any(t.type == "surface" for t in fig.data)
