from braidpy.material_braid import MaterialStrand, MaterialBraid
import pytest


def test_init():
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.05)
    s2 = MaterialStrand(lambda t: (10, 0, t), radius=0.05)
    b = MaterialBraid((s1, s2))
    assert b.n_strands == 2


def test_init_too_close():
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.1)
    s2 = MaterialStrand(lambda t: (0.15, 0, t), radius=0.1)
    with pytest.raises(ValueError):
        MaterialBraid((s1, s2))


def test_are_too_close_false():
    # Two strands far apart
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.05)
    s2 = MaterialStrand(lambda t: (10, 0, t), radius=0.05)
    assert not MaterialBraid._are_too_close(s1, s2, clearance=0.01)


def test_are_too_close_true():
    # Two strands too close
    s1 = MaterialStrand(lambda t: (0, 0, t), radius=0.1)
    s2 = MaterialStrand(lambda t: (0.15, 0, t), radius=0.1)
    assert MaterialBraid._are_too_close(s1, s2, clearance=0.01)
