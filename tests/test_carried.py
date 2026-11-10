# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid made by its carriers: braidpy.carried."""

import math

import numpy as np
import pytest

from braidpy.carried import RADIUS, braid_by_carriers, figure
from braidpy.machine_catalog import CATALOGUE

# Steps of the flat plait, enough for its first crossings to be taken off.
STEPS = 8


@pytest.fixture(scope="module")
def plait():
    return braid_by_carriers(CATALOGUE["flat_3"].make(), STEPS)


def _crossings(yarns, n=4000):
    """A flat braid's crossings, oldest first: neighbours across x swapping,
    signed by which passes nearer, as flat_word signs them."""
    lo = max(y[:, 2].min() for y in yarns)
    hi = min(y[:, 2].max() for y in yarns)
    zs = np.linspace(hi, lo, n)
    at = np.stack(
        [
            np.stack(
                [
                    np.interp(zs, y[np.argsort(y[:, 2]), 2], y[np.argsort(y[:, 2]), c])
                    for c in (0, 1)
                ],
                axis=1,
            )
            for y in yarns
        ],
        axis=1,
    )
    order = list(np.argsort(at[0, :, 0]))
    word = []
    for k in range(1, n):
        for j in range(len(order) - 1):
            a, b = order[j], order[j + 1]
            if at[k, a, 0] > at[k, b, 0]:
                word.append((j + 1) * (1 if at[k, a, 1] < at[k, b, 1] else -1))
                order[j], order[j + 1] = b, a
    return word


@pytest.mark.slow
def test_the_plait_made_has_the_machines_crossings(plait):
    """Read above the ring, the braid the carriers made crosses as the braid
    laid off the machine does, crossing for crossing, its first ones made."""
    from braidpy.horn_gear import yarn_paths

    above = [y[y[:, 2] > plait.ring["height"] + 2 * RADIUS] for y in plait.yarns]
    made = _crossings(above)
    laid = _crossings(
        [
            np.asarray(p)
            for p in yarn_paths(
                CATALOGUE["flat_3"].make(), n_steps=STEPS
            ).points.values()
        ]
    )
    assert len(made) >= STEPS // 3
    assert made == laid[: len(made)]


@pytest.mark.slow
def test_the_yarns_pass_inside_the_ring_and_reach_their_carriers(plait):
    ring = plait.ring
    for k, yarn in enumerate(plait.yarns):
        r = np.hypot(yarn[:, 0], yarn[:, 1])
        from_wire = np.hypot(r - ring["radius"], yarn[:, 2] - ring["height"])
        assert from_wire.min() >= 0.95 * (ring["wire"] + RADIUS)
        # Inside it, where it crosses the ring's height.
        level = np.argmin(abs(yarn[:, 2] - ring["height"]))
        assert r[level] < ring["radius"]
        assert plait.eyes[k][2] == 0
    assert math.isfinite(plait.deepest)


@pytest.mark.slow
@pytest.mark.parametrize("view", ["braid", "machine"])
def test_the_braid_is_drawn_near_and_to_scale(plait, view):
    fig = figure(plait, view)
    names = {t.name for t in fig.data}
    assert "Forming ring" in names
    assert ("Carriers" in names) == (view == "machine")


def test_a_view_is_braid_or_machine():
    with pytest.raises(ValueError, match="braid' or 'machine"):
        figure(None, "side")
