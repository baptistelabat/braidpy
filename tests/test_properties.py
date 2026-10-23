# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from sympy import symbols

t = symbols("t")
# Run tests with: uv run pytest /tests


# class TestProperties:
#     def test_alexander_polynomial(self, simple_braid):
#         """Test Alexander polynomial calculation"""
#         t = symbols("t")
#         poly = alexander_polynomial(Braid([1, 1, 1]))
#         assert simplify(poly - (t**2 - t + 1)) == 0
#
#     def test_conjugacy_class(self, conjugate_braids):
#         """Test conjugacy class generation"""
#         b1, b2 = conjugate_braids
#         class_b1 = conjugacy_class(b1)
#
#         # Both braids should be in each other's conjugacy class
#         assert b2 in class_b1
#
#     def test_garside_normal_form(self, simple_braid):
#         """Test Garside normal form calculation"""
#         pos, neg = garside_normal_form(simple_braid)
#         assert pos == [1, 2]
#         assert neg == [-1]


import pytest

from braidpy import Braid, alexander_polynomial


@pytest.mark.parametrize(
    "word, n_strands, expected",
    [
        # Rolfsen's table: trefoil, figure eight, 5₁.
        ([1, 1, 1], 2, t**2 - t + 1),
        ([1, -2, 1, -2], 3, t**2 - 3 * t + 1),
        ([1] * 5, 2, t**4 - t**3 + t**2 - t + 1),
        # Hopf link: Δ = t − 1, up to sign.
        ([1, 1], 2, t - 1),
        # Borromean rings: Conway polynomial z⁴, z = t^½ − t^-½.
        ([1, -2] * 3, 3, (t - 1) ** 4),
        # Unknots, on any number of strands (Markov's theorem).
        ([], 1, 1),
        ([1], 2, 1),
        ([1, 2], 3, 1),
        # Loops that pull apart: a split link, Δ = 0.
        ([], 2, 0),
        ([], 3, 0),
    ],
)
def test_alexander_polynomial_of_known_closures(word, n_strands, expected):
    poly = alexander_polynomial(Braid(word, n_strands))
    assert (poly.as_expr() - expected).expand() == 0


def test_alexander_polynomial_does_not_see_the_starting_point_nor_the_mirror():
    """Conjugate braids close up alike; a mirror image has the same Δ."""
    word = [1, -2, 1, 1, -2, 2]
    rotated = word[2:] + word[:2]
    mirrored = [-g for g in word]
    expected = alexander_polynomial(Braid(word, 3))
    assert alexander_polynomial(Braid(rotated, 3)) == expected
    assert alexander_polynomial(Braid(mirrored, 3)) == expected


def test_a_negative_crossing_on_two_strands_is_the_inverse():
    """σ₁⁻¹ on two strands: the reduced Burau matrix is −1/t, not −t."""
    assert (Braid([1, -1], 2).to_reduced_matrix()[0, 0] - 1) == 0
