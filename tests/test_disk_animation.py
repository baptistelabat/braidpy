# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braiding disk, animated from above."""

import matplotlib
import numpy as np
import pytest

from braidpy.disk_animation import (
    animate_disk,
    animate_kumihimo,
    animate_mobidai,
    kumihimo_step_labels,
)
from braidpy.kumihimo import Kumihimo
from braidpy.mobidai import MobidaiConfig, Move, Strand
from braidpy.take_off import disk_trajectories

matplotlib.use("Agg")


def _spokes(frame, n):
    """The frame's spokes drawn under, then over, then the carriers.

    Between the two sit the white edgings of the copies drawn over.
    """
    return frame.data[:n], frame.data[2 * n : 3 * n], frame.data[3 * n]


def _edgings(frame, n):
    return frame.data[n : 2 * n]


def test_strands_are_spokes_to_their_carriers():
    traj = disk_trajectories({0: 1, 1: 3}, [{0: 4}], n_slots=8, samples_per_step=4)
    fig = animate_disk(traj)
    assert len(fig.frames) == 5
    for frame, index in zip(fig.frames, range(5)):
        under, _, carriers = _spokes(frame, 2)
        for k, spoke in enumerate(under):
            assert spoke.x[0] == spoke.y[0] == 0.0  # from the braiding point
            assert [spoke.x[1], spoke.y[1]] == pytest.approx(
                traj.xy[k][index], abs=1e-4
            )
        assert list(carriers.text) == ["0", "1"]


def test_a_strand_lifted_over_is_drawn_on_top():
    traj = disk_trajectories({0: 1, 1: 3}, [{0: 4}], n_slots=8, samples_per_step=4)
    fig = animate_disk(traj)
    # At rest nobody is lifted; half way through the move strand 0 is.
    _, over, _ = _spokes(fig.frames[0], 2)
    assert all(list(s.x) == [None, None] for s in over)
    _, over, _ = _spokes(fig.frames[2], 2)
    assert None not in over[0].x and list(over[1].x) == [None, None]
    assert np.hypot(over[0].x[1], over[0].y[1]) < 1.0  # inside the rim


def test_a_moving_strand_keeps_its_look_and_its_edging_swells_smoothly():
    """Nothing about a strand jumps as it is lifted or set down."""
    traj = disk_trajectories({0: 1, 1: 3}, [{0: 4}], n_slots=8, samples_per_step=8)
    fig = animate_disk(traj)
    widths = []
    for frame in fig.frames:
        under, over, _ = _spokes(frame, 2)
        # Under and over drawn alike: switching between them changes nothing.
        assert under[0].line.width == over[0].line.width == 3
        assert under[0].line.color == over[0].line.color
        assert under[0].opacity is None
        edging = _edgings(frame, 2)[0]
        widths.append(edging.line.width if edging.x[0] is not None else 3)
    # The edging grows to the middle of the move and shrinks back, by steps
    # no bigger than the move's own.
    middle = widths.index(max(widths))
    assert widths[: middle + 1] == sorted(widths[: middle + 1])
    assert widths[middle:] == sorted(widths[middle:], reverse=True)
    assert max(abs(a - b) for a, b in zip(widths, widths[1:])) < 3
    assert widths[0] == widths[-1] == 3


def test_a_strand_set_down_leaves_no_copy_behind():
    """Every frame says where each overlay is, so none outlives its lift.

    Plotly leaves a trace as it was when a frame gives it no points: an
    empty overlay once the move ended kept the lifted spoke on screen, a
    second copy of the strand, until the next lift moved it.
    """
    traj = disk_trajectories(
        {0: 1, 1: 3}, [{0: 4}, {}, {1: -1}], n_slots=8, samples_per_step=4
    )
    fig = animate_disk(traj)
    for frame in fig.frames:
        _, over, _ = _spokes(frame, 2)
        assert all(len(s.x) == 2 and len(s.y) == 2 for s in over)
        assert all(len(s.x) == 2 for s in _edgings(frame, 2))
    # Once strand 0 is set down its overlay is a gap, not its last position.
    _, over, _ = _spokes(fig.frames[4], 2)
    assert list(over[0].x) == [None, None]


def test_long_sequences_are_sampled_within_the_budget():
    traj = disk_trajectories({0: 1}, [{0: 1}] * 50, n_slots=8, samples_per_step=12)
    fig = animate_disk(traj, max_frames=100)
    assert len(fig.frames) <= 101
    assert fig.frames[-1].name == str(len(traj.times) - 1)


def test_kumihimo_animation(tmp_path):
    kumihimo = Kumihimo(8).move("SR")
    out = tmp_path / "kumihimo.html"
    fig = kumihimo.animate(output_html=str(out), samples_per_step=4)
    assert out.exists()
    # A swap is three disk steps and a turn one: 4 steps of 4 samples, + 1.
    assert len(fig.frames) == 17
    labels = [s.label for s in fig.layout.sliders[0].steps if s.label]
    assert labels == ["0 S (top over)", "1 S (bottom over)", "2 S (settle)", "3 R"]
    assert "SR" in fig.layout.title.text
    # One colour per strand, none repeated.
    _, _, carriers = _spokes(fig.frames[0], 8)
    assert len(set(carriers.marker.color)) == 8


def test_kumihimo_from_a_pattern():
    fig = animate_kumihimo("SRSR", n_strands=12, samples_per_step=2)
    assert len(fig.frames) == 8 * 2 + 1
    assert kumihimo_step_labels("RS") == [
        "R",
        "S (top over)",
        "S (bottom over)",
        "S (settle)",
    ]
    with pytest.raises(ValueError):
        kumihimo_step_labels("S", n_strands=6)


def test_mobidai_animation():
    config = MobidaiConfig(
        strands=[Strand(c, p) for c, p in [("red", 1), ("green", 2), ("blue", 6)]],
        moves=[Move(1, 4)],
        n_shift_after_cycle=1,
        n_slots=8,
    )
    fig = animate_mobidai(config, n_cycles=2, samples_per_step=3)
    labels = [s.label.split(" ", 1)[1] for s in fig.layout.sliders[0].steps if s.label]
    assert labels == ["move", "turn", "turn"]  # slot 1 is empty the second time
    _, _, carriers = _spokes(fig.frames[0], 3)
    assert list(carriers.marker.color) == ["red", "green", "blue"]
