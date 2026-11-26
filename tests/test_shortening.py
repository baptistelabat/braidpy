# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid word made shorter: braidpy.shortening."""

import random

import pytest

from braidpy import Braid
from braidpy.shortening import free_reduced, rewrites, shortened


def test_a_crossing_and_its_inverse_side_by_side_cancel():
    assert free_reduced((1, 2, -2, -1, 3)) == (3,)
    assert free_reduced((1, -2, 3)) == (1, -2, 3)


@pytest.mark.parametrize(
    "word",
    [(1, 3), (1, 2, 1), (1, 2, -1), (-1, 2, 1), (-1, -2, -1), (2, 1, -2), (1, -2, -1)],
)
def test_each_rewrite_is_the_same_braid(word):
    """Swapping crossings of strands apart, and the three of three strands
    the other way round, signs mixed or not: the braid does not change."""
    braid = Braid(word, 4)
    rewritten = list(rewrites(word))
    assert rewritten
    for other in rewritten:
        assert len(other) == len(word)
        assert Braid(other, 4) == braid


def test_crossings_kept_apart_are_brought_together_and_cancel():
    """σ₁ σ₃ σ₁⁻¹: σ₃ moves out of the way, and σ₁ σ₁⁻¹ cancel; σ₁ σ₂ σ₁
    σ₂⁻¹ σ₁⁻¹ σ₂⁻¹ is no braid at all."""
    assert shortened(Braid((1, 3, -1), 4)).generators == [3]
    assert shortened(Braid((1, 2, 1, -2, -1, -2), 3)).generators == []


def test_a_braid_padded_with_trivial_words_comes_back_shorter():
    """Words of no braid put into a braid's: they are taken out again,
    most of them, and the braid is the same."""
    rng = random.Random(1)
    braid = Braid((1, -2) * 6, 4)
    padding = ([1, 2, 1, -2, -1, -2], [2, 3, 2, -3, -2, -3], [1, 3, -1, -3])
    word = list(braid.generators)
    for _ in range(6):
        at = rng.randrange(len(word) + 1)
        word[at:at] = rng.choice(padding)
    found = shortened(Braid(tuple(word), 4))
    assert len(found.generators) < len(word) - 20
    assert found == braid


def test_random_words_shortened_are_the_same_braid_and_no_longer():
    rng = random.Random(0)
    for _ in range(40):
        n = rng.randint(2, 5)
        word = [rng.choice((-1, 1)) * rng.randint(1, n - 1) for _ in range(12)]
        braid = Braid(word, n)
        found = shortened(braid)
        assert len(found.generators) <= len(word)
        assert found.n_strands == n
        assert found == braid


def test_a_word_of_one_sign_is_as_short_as_it_gets():
    """The relations keep the sum of a word's signs: a positive word cannot
    be shorter, and is kept as it is."""
    braid = Braid((1, 2, 1, 2, 3, 1), 4)
    assert shortened(braid).generators == braid.generators


def test_the_braid_method_is_the_same():
    braid = Braid((1, 3, -1, 2), 4)
    assert braid.shortened().generators == shortened(braid).generators


def test_moves_round_a_ring_are_shortened_round_the_core():
    """Round a ring, the wrapping crossing is a neighbour like any other and
    a turn passes a crossing by renumbering it: each rewrite, and the word
    shortened, is the same braid round the core, exactly."""
    from braidpy.annulus_braid import cored_word
    from braidpy.shortening import shortened_ring

    rng = random.Random(1)
    shorter = 0
    for _ in range(60):
        n = rng.randint(2, 5)
        word = tuple(
            rng.choice((-1, 1)) * rng.randint(1, n + 1)
            for _ in range(rng.randint(2, 10))
        )
        braid = Braid(tuple(cored_word(word, n)), n + 1)
        for other in rewrites(word, n):
            assert len(other) == len(word)
            assert Braid(tuple(cored_word(other, n)), n + 1) == braid
        found = shortened_ring(word, n)
        assert len(found) <= len(word)
        assert Braid(tuple(cored_word(found, n)), n + 1) == braid
        shorter += len(found) < len(word)
    assert shorter > 20


def test_crossings_far_apart_round_a_ring_are_not_far_apart_on_a_line():
    """σ₁ and σ₄ of five strands commute on a line; round a ring of four
    slots, crossing 4 is crossing 1's neighbour."""
    assert (3, 1) in set(rewrites((1, 3), 4)) and (4, 1) not in set(rewrites((1, 4), 4))
    assert (4, 1) in set(rewrites((1, 4)))
