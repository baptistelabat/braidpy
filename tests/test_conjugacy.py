# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy.conjugacy: whether two braids are the same however written."""

import itertools
import random

import pytest

from braidpy.braid import Braid
from braidpy.conjugacy import (
    SuperSummitSetTooLarge,
    _word,
    are_conjugate,
    same_braid,
    super_summit_set,
)
from braidpy.garside_canonical_form import artin_left_normal_form, left_weighted


def _inverse(word):
    return [-g for g in reversed(word)]


def test_left_weighted_gives_the_normal_form_of_any_product():
    """Permutation braids in any order, the half twist and the identity
    among them, are the braid their words make."""
    rng = random.Random(0)
    for _ in range(100):
        n = rng.randint(2, 6)
        factors = [tuple(rng.sample(range(n), n)) for _ in range(rng.randint(0, 5))]
        k = rng.randint(-2, 2)
        assert left_weighted(k, factors) == artin_left_normal_form(
            _word((k, tuple(factors)), n), n
        )


def test_a_braid_is_conjugate_to_itself_read_from_anywhere():
    """``c⁻¹ a c`` for random ``a`` and ``c``: conjugate."""
    rng = random.Random(1)
    for _ in range(40):
        n = rng.randint(3, 5)
        a = [rng.choice([-1, 1]) * rng.randint(1, n - 1) for _ in range(8)]
        c = [rng.choice([-1, 1]) * rng.randint(1, n - 1) for _ in range(5)]
        assert are_conjugate(Braid(a, n), Braid(_inverse(c) + a + c, n))


def test_conjugacy_agrees_with_trying_every_short_conjugator():
    """On three strands, braids of up to five crossings: conjugate by the
    proof exactly when some conjugator of up to four crossings makes one
    the other — which, so short, it always does here."""
    n, gens = 3, [1, -1, 2, -2]
    conjugators = [list(c) for k in range(5) for c in itertools.product(gens, repeat=k)]
    rng = random.Random(3)
    words = [[rng.choice(gens) for _ in range(rng.randint(2, 5))] for _ in range(20)]
    for a in words:
        tried = {artin_left_normal_form(_inverse(c) + a + c, n) for c in conjugators}
        for b in words:
            found = artin_left_normal_form(b, n) in tried
            assert are_conjugate(Braid(a, n), Braid(b, n)) == found


def test_every_braid_of_a_super_summit_set_finds_the_same_set():
    braid = Braid([1, -2, 3, 1, -2, -3, 2], 4)
    whole = super_summit_set(braid)
    assert len(whole) > 1
    for x in whole:
        assert super_summit_set(Braid(_word(x, 4), 4)) == whole


def test_the_plait_is_its_own_mirror_read_another_way():
    """σ₁σ₂⁻¹ and σ₂⁻¹σ₁ are one braid read from two starting points;
    σ₁σ₂ is another braid."""
    assert same_braid(Braid([1, -2], 3), Braid([-2, 1], 3))
    assert not same_braid(Braid([1, -2], 3), Braid([1, 2], 3))


def test_numbering_the_strands_from_the_other_side_is_conjugation():
    word = [1, 2, -3, 1, -2]
    flipped = [(4 - abs(g)) * (1 if g > 0 else -1) for g in word]
    assert are_conjugate(Braid(word, 4), Braid(flipped, 4))


@pytest.mark.parametrize(
    "a, b, n",
    [
        # Edo yatsu and ABOK #3070.
        (
            [7, 6, 5, 4, 3, 2, -3, -5, -7, -1, -2, -3, -4, -5, -6, 5, 3, 1],
            [6, 5, -3, -4, -5, -6, -7, 5, 4, 3, 2, 1, -3, -4],
            8,
        ),
        # A flat braid of six and ABOK #3021.
        (
            [-4, -3, -2, 1, 2, 3, 2, 3, 4, -5, -4, -3],
            [5, 3, -2, -3, -4, -5, 4, 3, 2, 1, -2, -4],
            6,
        ),
    ],
)
@pytest.mark.slow
def test_braids_alike_in_every_number_measured_are_proven_different(a, b, n):
    """Their loops, writhe and linking numbers are equal and their
    Alexander polynomials vanish: the fingerprint told them apart only once
    it held the Burau polynomial.  The search tells them apart without it."""
    assert not are_conjugate(Braid(a, n), Braid(b, n))
    assert not same_braid(Braid(a, n), Braid(b, n))


def test_a_search_too_large_says_so():
    with pytest.raises(SuperSummitSetTooLarge):
        super_summit_set(Braid([1, -2, 3, -4, 5, -6, 7], 8), limit=2)


@pytest.mark.slow
def test_braids_repeated_as_often_are_compared_by_their_units():
    """ABOK #3057's unit closes after 20 repeats, 460 crossings: compared by
    the unit instead, read from another starting point, it is found the
    same."""
    unit = [7, 6, 5, 4, 3, 7, 6, 5, 4, -6, -7, -8, 4, 3, 2, 1, -3, -4, -5]
    unit += [-2, -3, -4, -5]
    turned = unit[5:] + unit[:5]
    assert same_braid(Braid(unit * 2, 9), Braid(turned, 9))
