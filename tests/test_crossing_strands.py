"""
test_crossing_strands.py
========================
Pytest unit test suite for TwoStrandCrossingModel in braidpy.

Run via:
    pytest test_crossing_strands.py
    # or
    python -m pytest test_crossing_strands.py -v
"""

import numpy as np
import pytest
from braidpy_crossing_strands import TwoStrandCrossingModel


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
    assert deviation < 0.05, f"Strand 1 is not straight under high tension: dev={deviation:.4f} mm"


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

    assert deviation < 0.05, f"Strand 2 is not straight under high tension: dev={deviation:.4f} mm"


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


def test_braidpy_callables():
    """Verify to_braidpy_strands() returns two callables evaluating in 3D for braidpy."""
    model = TwoStrandCrossingModel(disk_radius=1.8)
    s1_fn, s2_fn = model.to_braidpy_strands()

    assert callable(s1_fn), "s1_fn must be callable"
    assert callable(s2_fn), "s2_fn must be callable"

    p1 = s1_fn(0.0)
    p2 = s2_fn(0.0)
    assert len(p1) == 3, "s1_fn must return 3D vector [x, y, z]"
    assert len(p2) == 3, "s2_fn must return 3D vector [x, y, z]"