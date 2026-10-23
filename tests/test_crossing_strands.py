# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Two strands crossing between two rotating disks:
braidpy.crossing_strands."""

import numpy as np
import pytest

from braidpy.crossing_strands import TwoStrandCrossingModel
from braidpy.parametric_strand import ParametricStrand


def test_simplified_circular_non_penetration():
    """
    Test Simplified Case (Pure circular cylinders, flattening_ratio = 1.0).
    Verifies that the surface clearance gap is >= 0 for all twist angles:
    from 0° untwisted up to 720° multi-turn spirals.
    """
    twist_angles = [0.0, 45.0, 90.0, 154.0, 180.0, 270.0, 360.0, 540.0, 720.0]
    for phi in twist_angles:
        model = TwoStrandCrossingModel(
            disk_radius=1.8,
            radius1=0.4,
            radius2=0.4,
            flattening_ratio=1.0,  # Pure circular cylinders (without flattening)
            spiral_angle_deg=phi,
            tension1=1.0,
            tension2=1.0,
        )
        res = model.compute_contact_clearance(n_samples=201)
        assert res["surface_gap"] >= -1e-3, (
            f"Physical penetration detected at phi={phi}°: gap={res['surface_gap']:.5f} mm"
        )
        assert not res["has_penetration"], f"has_penetration flag set at phi={phi}°"


def test_flattened_elliptical_non_penetration():
    """
    Test General Case with Contact Flattening (flattening_ratio = 0.75).
    Verifies that the flattened elliptical faces press flush against each other
    without interpenetration along the dynamic contact normal.
    """
    for phi in [180.0, 360.0, 540.0, 720.0]:
        model = TwoStrandCrossingModel(
            disk_radius=1.8,
            radius1=0.4,
            radius2=0.4,
            flattening_ratio=0.75,  # Flattened tape / compacted braid
            spiral_angle_deg=phi,
            tension1=1.0,
            tension2=1.0,
        )
        res = model.compute_contact_clearance(n_samples=201)
        assert res["surface_gap"] >= -1e-3, (
            f"Interpenetration in flattened case at phi={phi}°: gap={res['surface_gap']:.5f} mm"
        )


def test_tension_asymmetry_high_t1_straight_strand():
    """
    When T1 >> T2 (e.g. 10.0 N vs 0.1 N, ratio 100:1), Strand 1 must be nearly straight
    between its disk anchor pins, and Strand 2 circles around it.
    """
    model = TwoStrandCrossingModel(
        disk_radius=1.8,
        radius1=0.4,
        radius2=0.4,
        flattening_ratio=1.0,
        spiral_angle_deg=360.0,
        tension1=10.0,
        tension2=0.1,
    )

    # Strand 1 positions at bottom, midpoint, and top
    p_bot = model.eval_disk_helix_position(1, -1.0)
    p_mid = model.eval_disk_helix_position(1, 0.0)
    p_top = model.eval_disk_helix_position(1, 1.0)

    # Midpoint of the straight chord connecting the two disk anchor pins
    chord_mid = 0.5 * (p_bot + p_top)
    deviation = float(np.linalg.norm(p_mid - chord_mid))

    # Taut strand 1 should have minimal deviation (< 0.05 mm) from chord
    assert deviation < 0.05, (
        f"Strand 1 is not straight under high tension: dev={deviation:.4f} mm"
    )


def test_tension_asymmetry_high_t2_straight_strand():
    """
    When T2 >> T1 (e.g. 0.1 N vs 10.0 N, ratio 1:100), Strand 2 must be nearly straight
    between its disk anchor pins, and Strand 1 circles around it.
    """
    model = TwoStrandCrossingModel(
        disk_radius=1.8,
        radius1=0.4,
        radius2=0.4,
        flattening_ratio=1.0,
        spiral_angle_deg=360.0,
        tension1=0.1,
        tension2=10.0,
    )

    # Strand 2 positions at bottom, midpoint, and top
    p_bot = model.eval_disk_helix_position(2, -1.0)
    p_mid = model.eval_disk_helix_position(2, 0.0)
    p_top = model.eval_disk_helix_position(2, 1.0)

    chord_mid = 0.5 * (p_bot + p_top)
    deviation = float(np.linalg.norm(p_mid - chord_mid))

    assert deviation < 0.05, (
        f"Strand 2 is not straight under high tension: dev={deviation:.4f} mm"
    )


def test_regime1_straight_parallel_lines():
    """At 0° twist angle, both strands must be straight parallel lines separated by 2*R_disk."""
    model = TwoStrandCrossingModel(
        disk_radius=1.8,
        radius1=0.4,
        radius2=0.4,
        flattening_ratio=1.0,
        spiral_angle_deg=0.0,
    )
    expected_sep = 2.0 * 1.8
    for t in np.linspace(-1.0, 1.0, 21):
        p1 = model.eval_disk_helix_position(1, float(t))
        p2 = model.eval_disk_helix_position(2, float(t))
        dist = float(np.linalg.norm(p1 - p2))
        assert np.isclose(dist, expected_sep, atol=1e-5), (
            f"Distance at t={t} is {dist:.4f}, expected {expected_sep:.4f}"
        )


def test_braidpy_parametric_strands():
    """The strands as braidpy's ParametricStrand, over [0, 1] from bottom pin
    to top pin."""
    model = TwoStrandCrossingModel(disk_radius=1.8, spiral_angle_deg=360.0)
    strands = model.to_parametric_strands()
    assert len(strands) == 2
    for k, strand in enumerate(strands, start=1):
        assert isinstance(strand, ParametricStrand)
        for s, t in [(0.0, -1.0), (0.5, 0.0), (1.0, 1.0)]:
            assert np.allclose(strand.evaluate(s), model.eval_disk_helix_position(k, t))


@pytest.mark.parametrize("tensions", [(1.0, 1.0), (10.0, 0.1), (0.1, 10.0), (3.0, 1.0)])
@pytest.mark.parametrize("flattening", [1.0, 0.75])
def test_no_penetration_whatever_the_tensions(tensions, flattening):
    """Strands that wind round each other pass closest at different heights:
    unequal tensions used to bring them up to 0.03 closer than they touch, at
    every pair of heights sampled finer than the model settles with."""
    for phi in range(0, 1081, 90):
        model = TwoStrandCrossingModel(
            flattening_ratio=flattening,
            spiral_angle_deg=phi,
            tension1=tensions[0],
            tension2=tensions[1],
        )
        res = model.compute_contact_clearance(n_samples=601)
        assert res["surface_gap"] >= -2e-3, (phi, res["surface_gap"])


def test_the_strands_touch_once_wound():
    """Widened no more than it must be: past the critical angle the strands
    touch, within sampling."""
    model = TwoStrandCrossingModel(flattening_ratio=1.0, spiral_angle_deg=360.0)
    assert model.compute_contact_clearance(n_samples=401)["surface_gap"] < 0.02


def test_the_frame_is_orthonormal_and_faces_the_other_strand():
    model = TwoStrandCrossingModel(spiral_angle_deg=360.0)
    for t in (-0.9, -0.2, 0.0, 0.5):
        f = model.eval_strand(1, t)
        frame = np.array([f["tangent"], f["normal"], f["binormal"]])
        assert np.allclose(frame @ frame.T, np.eye(3), atol=1e-6)
        towards = model.eval_disk_helix_position(2, t) - f["pos"]
        assert np.dot(towards, f["normal"]) > 0
