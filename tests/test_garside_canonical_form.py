# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

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
