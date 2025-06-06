from braidpy.garside_canonical_form import GarsideCanonicalFactors


def test_init():
    GarsideCanonicalFactors(n_half_twist=2, n_strands=5, Ai=[])

    GarsideCanonicalFactors(n_half_twist=2, n_strands=5, Ai=[1, 2])


def test_floor():
    assert (
        GarsideCanonicalFactors(n_half_twist=2, n_strands=5, Ai=[1, 2]).dehornoy_floor
        == 1
    )


def test_length():
    assert (
        GarsideCanonicalFactors(n_half_twist=2, n_strands=5, Ai=[1, 2]).garside_length
        == 2
    )
