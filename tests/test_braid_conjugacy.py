# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Comparing braids up to where you start reading them."""

import random

import pytest

from braidpy.braid_conjugacy import (
    TooManyConjugates,
    are_conjugate,
    canonical,
    conjugate,
    cycling,
    decycling,
    inverse_word,
    invariants,
    least_rotation,
    normal_form,
    summit,
    super_summit_set,
    to_word,
)


def rotations(word):
    return [word[i:] + word[:i] for i in range(len(word))]


# ── the word problem, which normal form already settles ──────────────────────


def test_a_word_and_its_normal_form_spell_the_same_braid():
    for word, n in (([1, -2, 1], 3), ([1, 3, 2, -1], 4), ([], 3)):
        form = normal_form(word, n)
        assert normal_form(to_word(form, n), n) == form


def test_the_braid_relation_does_not_change_the_normal_form():
    """s1 s2 s1 and s2 s1 s2 are one braid, written two ways."""
    assert normal_form([1, 2, 1], 3) == normal_form([2, 1, 2], 3)


def test_far_generators_commute():
    assert normal_form([1, 3], 4) == normal_form([3, 1], 4)


# ── why the word's own least rotation is not enough ──────────────────────────


def test_least_rotation_is_the_smallest_way_round_the_circle():
    for word in ([3, 1, 2, 1], [2, 2, 1], [1], [], [2, 1, 2, 1]):
        got = least_rotation(word)
        assert got == min(rotations(word)) if word else got == []
        assert sorted(got) == sorted(word)


def test_least_rotation_does_not_decide_braids():
    """The point of the whole module: equal braids, different least rotations.

    s1 s2 s1 and s2 s1 s2 are the same braid, but no rotation of one is the
    other, so a canonical form built on the word alone calls them different.
    """
    assert normal_form([1, 2, 1], 3) == normal_form([2, 1, 2], 3)
    assert least_rotation([1, 2, 1]) != least_rotation([2, 1, 2])
    # the conjugacy canonical form is not fooled
    assert canonical([1, 2, 1], 3) == canonical([2, 1, 2], 3)


# ── cycling and decycling ────────────────────────────────────────────────────


def test_cycling_and_decycling_stay_in_the_conjugacy_class():
    word = [1, -2, 1, 1, -2]
    form = normal_form(word, 3)
    for moved in (cycling(form, 3), decycling(form, 3)):
        assert are_conjugate(word, to_word(moved, 3), 3)


def test_cycling_does_not_lower_inf_and_decycling_does_not_raise_sup():
    rng = random.Random(0)
    for _ in range(20):
        word = [rng.choice([1, -1, 2, -2]) for _ in range(rng.randrange(1, 8))]
        form = normal_form(word, 3)
        assert invariants(cycling(form, 3))["inf"] >= invariants(form)["inf"]
        assert invariants(decycling(form, 3))["sup"] <= invariants(form)["sup"]


def test_the_summit_is_where_cycling_and_decycling_stop_helping():
    word = [1, -2, 1, 1, -2, 2, 1]
    top = summit(normal_form(word, 3), 3)
    assert invariants(cycling(top, 3))["inf"] == invariants(top)["inf"]
    assert invariants(decycling(top, 3))["sup"] == invariants(top)["sup"]
    assert are_conjugate(word, to_word(top, 3), 3)


# ── the comparison asked for ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word,n",
    [
        ([1, -2, 1, -2, 1, -2], 3),
        ([1, 1, 2, -1], 3),
        ([1, 2, 3, -2], 4),
    ],
)
def test_reading_a_braid_from_any_step_gives_the_same_canonical_form(word, n):
    """Offsetting the word is conjugation, which is what this sees through."""
    forms = {canonical(rot, n) for rot in rotations(word)}
    assert len(forms) == 1
    for rot in rotations(word):
        assert are_conjugate(word, rot, n)


def test_a_braid_is_conjugate_to_anything_it_is_conjugated_by():
    rng = random.Random(1)
    word = [1, -2, 1, 1]
    for _ in range(8):
        by = [rng.choice([1, -1, 2, -2]) for _ in range(rng.randrange(1, 5))]
        moved = conjugate(word, by, 3)
        assert are_conjugate(word, to_word(moved, 3), 3)


def test_braids_that_are_not_conjugate_are_told_apart():
    # different exponent sum cannot be conjugate: it is a class function
    assert not are_conjugate([1, 1], [1, 1, 1], 3)
    assert not are_conjugate([1], [-1], 3)
    assert not are_conjugate([1, 2], [1, -2], 3)


def test_the_invariants_agree_across_a_conjugacy_class():
    word = [1, -2, 1, -2]
    want = invariants(summit(normal_form(word, 3), 3))
    for rot in rotations(word):
        assert invariants(summit(normal_form(rot, 3), 3)) == want


def test_the_summit_set_holds_its_own_canonical_form():
    word = [1, -2, 1, 1]
    found = super_summit_set(word, 3)
    assert found
    assert canonical(word, 3) in found
    assert canonical(word, 3) == min(found)
    # every element of it is conjugate to the braid it came from
    for element in found:
        assert are_conjugate(word, to_word(element, 3), 3)


def test_the_identity_is_its_own_class():
    assert canonical([], 3) == canonical([1, -1], 3)
    assert are_conjugate([], [2, -2], 3)
    assert not are_conjugate([], [1], 3)


def test_a_runaway_search_says_so_rather_than_grinding():
    with pytest.raises(TooManyConjugates, match="super summit set"):
        super_summit_set([1, 2, 1, 2, 1, 2], 4, limit=1)


def test_inverse_word_undoes_a_braid():
    word = [1, -2, 3]
    assert normal_form(list(word) + inverse_word(word), 4) == normal_form([], 4)


@pytest.mark.parametrize("n", [3, 4])
def test_conjugating_at_random_never_changes_the_canonical_form(n):
    """The property the whole module stands on, checked by brute force.

    This is what caught `summit` giving up too early: inf can sit still for
    several cyclings before it rises, and stopping at the first that does not
    help left some braids short of their summit and gave them a canonical form
    of their own.
    """
    rng = random.Random(7)
    letters = [g for i in range(1, n) for g in (i, -i)]
    for _ in range(25):
        word = [rng.choice(letters) for _ in range(rng.randrange(1, 7))]
        want = canonical(word, n)
        for _ in range(3):
            by = [rng.choice(letters) for _ in range(rng.randrange(1, 5))]
            moved = to_word(conjugate(word, by, n), n)
            assert canonical(moved, n) == want, (word, by)
        for rot in rotations(word):
            assert canonical(rot, n) == want, (word, rot)


@pytest.mark.parametrize("n", [3, 4])
def test_the_summit_really_is_the_top(n):
    """Nothing in the class beats a summit element on inf or on sup."""
    rng = random.Random(11)
    letters = [g for i in range(1, n) for g in (i, -i)]
    for _ in range(15):
        word = [rng.choice(letters) for _ in range(rng.randrange(1, 7))]
        top = invariants(summit(normal_form(word, n), n))
        for element in super_summit_set(word, n):
            assert invariants(element)["inf"] == top["inf"]
            assert invariants(element)["sup"] == top["sup"]
