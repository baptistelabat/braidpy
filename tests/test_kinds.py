# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What "the same braid" means: braidpy.kinds."""

from braidpy import Braid
from braidpy.conjugacy import same_braid, same_pattern
from braidpy.kinds import BraidPattern, BraidWord, ClosedBraid

# σ₁σ₂σ₁ and σ₂σ₁σ₂: two words, one braid.
ONE = Braid((1, 2, 1), 3)
OTHER = Braid((2, 1, 2), 3)


def test_two_words_of_one_braid():
    assert ONE.word() != OTHER.word()
    assert ONE == OTHER
    assert len({ONE.word(), OTHER.word()}) == 2
    assert len({ONE, OTHER}) == 1


def test_a_word_writes_its_braid_back():
    word = BraidWord((1, -2), 3)
    assert word.braid().word() == word


def test_a_braid_read_from_another_start_is_another_braid_and_one_pattern():
    """σ₁σ₂ and σ₂σ₁ are conjugate: two braids, but made over and over,
    the same."""
    a, b = Braid((1, 2), 3), Braid((2, 1), 3)
    assert a != b
    assert a.pattern() == b.pattern()
    assert len({a.pattern(), b.pattern()}) == 1


def test_a_braid_and_its_square_are_one_pattern_and_two_links():
    """Made over and over, w and w w are the same; closed, one repeat of
    the plait closes into a plain loop, two into the figure-eight knot."""
    plait = Braid((1, -2), 3)
    twice = Braid((1, -2, 1, -2), 3)
    assert plait.pattern() == twice.pattern()
    assert plait.closed() != twice.closed()


def test_patterns_that_differ_are_proven_to():
    a, b = Braid((1, 2), 3), Braid((1, -2), 3)
    assert a.pattern().proven(b.pattern()) is False
    assert a.pattern() != b.pattern()


def test_a_closed_braid_does_not_care_how_many_strands():
    """σ₁ on two strands closes into one loop, as one strand does: two
    patterns, one knot (Markov)."""
    stabilised, strand = Braid((1,), 2), Braid((), 1)
    assert stabilised.pattern() != strand.pattern()
    assert stabilised.closed() == strand.closed()
    assert stabilised.closed().loops == 1
    # The trefoil, on two strands or three.
    assert Braid((1, 1, 1), 2).closed() == Braid((1, 1, 1, 2), 3).closed()


def test_a_closed_braid_counts_its_loops():
    assert Braid((1, -2) * 3, 3).closed().loops == 3  # the Borromean rings
    assert Braid((1, 1), 2).closed().loops == 2  # the Hopf link
    assert Braid((1, 1), 2).closed() != Braid((), 2).closed()  # linked, or not


def test_the_old_name_is_the_same_test():
    assert same_braid is same_pattern
    assert isinstance(ONE.pattern(), BraidPattern)
    assert isinstance(ONE.closed(), ClosedBraid)
