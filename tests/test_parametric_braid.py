# Create braid σ₁ σ₂⁻¹ σ₁ on 3 strands
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
