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


@pytest.mark.parametrize("n_generators", range(1, 31))
def test_a_strand_reaches_the_end_of_its_time_whatever_the_word_length(
    n_generators,
):
    """Every strand is defined over the whole of [0, 1], to its very end.

    Each generator takes 1 / (n_generators + 1) of the time; summed in
    floating point, the last segment can stop just short of 1 (for five
    generators, at 0.9999999999999999), and ``evaluate(1.0)`` then raised
    "Time 1.0 is out of bounds for this strand"."""
    word = [(-1) ** k * (1 + k % 3) for k in range(n_generators)]
    for strand in Braid(word, n_strands=4).to_parametric_strands():
        assert strand.evaluate(0.0)[2] == 0.0
        assert strand.evaluate(1.0)[2] == 1.0


def test_a_five_generator_word_can_be_laid_out():
    """The word the bug was found with, in Braid Studio."""
    strands = Braid((1, -3, 5, 2, -4), n_strands=6).to_parametric_strands()
    assert [strand.evaluate(1.0)[2] for strand in strands] == [1.0] * 6


def test_closest_approach_finds_the_tightest_spot():
    """A measurement on any strands at all, whoever made them.

    Strands of diameter d may not come closer than d, and nothing in a
    drawing enforces that — so it is measured rather than assumed.
    """
    import math

    from braidpy.annulus_braid import lay_radius, rope_helices
    from braidpy.parametric_braid import closest_approach

    diameter, lay = 0.4, 2.4
    touching = rope_helices(3, diameter=diameter, length=lay, turns=1.0)
    assert closest_approach(touching, 500) == pytest.approx(diameter, abs=2e-3)

    squeezed = rope_helices(
        3,
        diameter=diameter,
        length=lay,
        turns=1.0,
        radius=lay_radius(3, diameter, lay) * 0.8,
    )
    assert closest_approach(squeezed, 500) < diameter

    assert closest_approach(touching[:1]) == math.inf


def test_a_braid_can_be_drawn_as_yarn_rather_than_as_lines():
    """Tubes at the strands' real thickness, so the fit can be seen.

    A line drawing shows where the centres go and leaves whether the yarn
    touches or overlaps to be believed; this shows it.
    """
    from braidpy.annulus_braid import lay_radius, minimum_lay, rope_helices
    from braidpy.parametric_braid import ParametricBraid
    from braidpy.parametric_strand import ParametricStrand

    diameter = 0.4
    lay = minimum_lay(3, diameter) * 2
    helices = rope_helices(
        3,
        diameter=diameter,
        length=lay,
        turns=1.0,
        radius=lay_radius(3, diameter, lay),
    )
    braid = ParametricBraid(
        [
            ParametricStrand(lambda t, helix=helix: helix.position(t * helix.length))
            for helix in helices
        ]
    )

    lines = braid.figure(n_sample=60)
    assert [trace.type for trace in lines.data] == ["scatter3d"] * 3

    tubes = braid.figure(n_sample=60, tube_diameter=diameter)
    assert [trace.type for trace in tubes.data] == ["surface"] * 3
    assert all(trace.opacity < 1.0 for trace in tubes.data), "the far side shows"

    assert isinstance(
        braid.plot(n_sample=20, output_html=None, plotter="nothing"), ParametricBraid
    ), "plot still returns the braid"


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
