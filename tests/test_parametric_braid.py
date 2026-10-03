# Create braid σ₁ σ₂⁻¹ σ₁ on 3 strands
import math

import pytest
from braidpy import Braid
from braidpy.parametric_braid import (
    ParametricBraid,
)
from braidpy.parametric_strand import ParametricStrand


def test_conversion():
    b = Braid((1, 0, 0, -2), n_strands=3)
    strands = b.to_parametric_strands()
    p = ParametricBraid(strands)  # .plot()
    assert p.get_positions_at(0.5) == [
        (0.2, 0.0, 0.5),
        (0.0, 0.0, 0.5),
        (0.4, 0.0, 0.5),
    ]

    # Sample and print one of the strands
    for pt in strands[0].sample(10):
        print(pt)


def test_parametric_strand_sampling():
    # Line from (0, 0, 0) to (1, 0, 1)
    def func(t):
        return (t, 0.0, t)

    strand = ParametricStrand(func)
    samples = strand.sample(5)
    assert len(samples) == 5
    assert samples[0][0] == 0
    assert samples[-1][0] == 1.0


def test_braid_to_parametric_strands():
    b = Braid((1,), n_strands=2)
    strands = b.to_parametric_strands()
    assert len(strands) == 2
    p0 = strands[0].evaluate(0)
    assert isinstance(p0, tuple)
    assert len(p0) == 3


def test_a_tube_is_everywhere_its_own_radius_from_the_centreline():
    """Which is what makes the picture a measurement rather than a suggestion."""
    import numpy as np

    from braidpy.parametric_strand import tube_mesh

    radius = 0.2
    points = [(math.cos(t / 30), math.sin(t / 30), t / 40) for t in range(120)]
    x, y, z = tube_mesh(points, radius, n_around=12)
    centre = np.array(points)

    gaps = np.sqrt(
        (x - centre[:, None, 0]) ** 2
        + (y - centre[:, None, 1]) ** 2
        + (z - centre[:, None, 2]) ** 2
    )
    assert gaps.min() == pytest.approx(radius, abs=1e-12)
    assert gaps.max() == pytest.approx(radius, abs=1e-12)
    assert x.shape == (len(points), 13)
    assert np.allclose(x[:, 0], x[:, -1]), "the ring closes"


def test_the_two_renderings_are_of_the_same_tube():
    """Plotly wants a surface, matplotlib wants faces; both share the rings.

    The Cosserat animation grew its own tube builder before this existed, so
    the point of sharing is that the pictures cannot drift apart.
    """
    import numpy as np

    from braidpy.parametric_strand import tube_faces, tube_mesh, tube_rings

    points = [(math.cos(t / 30), math.sin(t / 30), t / 40) for t in range(60)]
    radius, n_around = 0.2, 12

    x, y, z = tube_mesh(points, radius, n_around=n_around)
    rings = tube_rings(points, radius, n_around=n_around)
    assert np.allclose(np.stack([x, y, z], axis=2), rings)

    faces = tube_faces(points, radius, n_around=n_around)
    assert len(faces) == (len(points) - 1) * n_around
    assert all(len(face) == 4 for face in faces)
    # A face spans two rings, so its first two corners belong to one
    # centreline point and its last two to the next.
    centre = np.array(points)
    for corner, belongs_to in zip(faces[0], (0, 0, 1, 1)):
        assert float(
            np.linalg.norm(np.array(corner) - centre[belongs_to])
        ) == pytest.approx(radius, abs=1e-9)

    assert len(tube_faces(points, radius, n_around=n_around, stride=4)) < len(faces)


def test_the_carried_frame_stays_square_to_itself():
    """Two vectors square to the curve and to each other, all the way along."""
    import numpy as np

    from braidpy.parametric_strand import transported_frame

    points = [(math.cos(t / 20), math.sin(t / 20) ** 3, t / 30) for t in range(80)]
    centre, normal, binormal = transported_frame(points)

    assert centre.shape == normal.shape == binormal.shape
    assert np.allclose(np.linalg.norm(normal, axis=1), 1.0)
    assert np.allclose(np.linalg.norm(binormal, axis=1), 1.0)
    assert np.allclose(np.einsum("ij,ij->i", normal, binormal), 0.0, atol=1e-12)


def test_a_tube_does_not_crease_where_the_strand_straightens():
    """Parallel transport rather than the Frenet frame, which flips there.

    A curve with an inflection has no well-defined Frenet normal at it; the
    carried frame turns smoothly through, so consecutive rings stay lined up.
    """
    import numpy as np

    from braidpy.parametric_strand import tube_mesh

    # An S-bend: curvature passes through zero in the middle.
    points = [(t / 50, math.sin(t / 25) ** 3, 0.0) for t in range(-80, 81)]
    x, y, z = tube_mesh(points, 0.05, n_around=8)
    rings = np.stack([x, y, z], axis=2)
    steps = np.linalg.norm(np.diff(rings, axis=0), axis=2).max(axis=1)
    assert steps.max() < 10 * float(np.median(steps)), "a crease would spike here"
