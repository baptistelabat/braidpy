# Create braid σ₁ σ₂⁻¹ σ₁ on 3 strands
from braidpy import Braid
from braidpy.material_braid import MaterialBraid, MaterialStrand
from braidpy.parametric_braid import braid_to_parametric_strands, ParametricBraid, ParametricStrand


# def test_conversion():
#     b = Braid((1, -2, 1), n_strands=3)
#     strands = braid_to_parametric_strands(b)
#     ParametricBraid(strands).plot()
#
#
#
#     # Sample and print one of the strands
#     for pt in strands[0].sample(10):
#         print(pt)

def test_parametric_strand_sampling():
    # Line from (0, 0, 0) to (1, 0, 1)
    func = lambda t: (t, 0.0, t)
    strand = ParametricStrand(func)
    samples = strand.sample(5)
    assert len(samples)== 5
    assert samples[0][0]==0
    assert samples[-1][0]==1.0

def test_braid_to_parametric_strands():
    b = Braid((1,), n_strands=2)
    strands = braid_to_parametric_strands(b)
    assert len(strands)==2
    p0 = strands[0].evaluate(0)
    p1 = strands[1].evaluate(0)
    assert isinstance(p0, tuple)
    assert len(p0)==3

def test_are_too_close_false():
    # Two strands far apart
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.05)
    s2 = MaterialStrand(lambda t: (10, 0, t), radius=0.05)
    assert not MaterialBraid.are_too_close(s1, s2, clearance=0.01)

def test_are_too_close_true():
    # Two strands too close
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.1)
    s2 = MaterialStrand(lambda t: (0.15, 0, t), radius=0.1)
    assert MaterialBraid.are_too_close(s1, s2, clearance=0.01)