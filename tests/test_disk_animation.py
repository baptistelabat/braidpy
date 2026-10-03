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
    """The frame's spokes drawn under, then over, then the carriers."""
    return frame.data[:n], frame.data[n : 2 * n], frame.data[2 * n]


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
    assert all(len(s.x) == 0 for s in over)
    _, over, _ = _spokes(fig.frames[2], 2)
    assert len(over[0].x) == 2 and len(over[1].x) == 0
    assert np.hypot(over[0].x[1], over[0].y[1]) < 1.0  # inside the rim


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
