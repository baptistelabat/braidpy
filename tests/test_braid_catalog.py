# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from braidpy.artin_generators import a
from braidpy.braid import Braid, slide_strand
from braidpy.braid_catalog import (
    abok_2974,
    asymmetric_flat4,
    double_flat3,
    flat3,
    flat5,
    flat6,
    full_twist_braid,
    garside_half_twist_braid,
    inverted_flat3,
    regular_flat6,
    square4,
    weave3,
)


def test_slide_strand():
    # b = slide_strand(n_slide=2)
    # b.draw()
    # assert b.perm() == [2, 3, 1]
    #
    # b = slide_strand(n_slide=2, sign=-1)
    # b.draw()
    # assert b.perm() == [2, 3, 1]
    #
    # # Check n_slide=1 slide corresponds to Artin's generator
    # n = 3
    # b = slide_strand(start_index=n, n_slide=1)
    #
    # b.draw()
    # a(n, n + 1).draw()
    # assert b.word_eq(a(n, n + 1))
    #
    # # Check the Artin relationship 2
    # n = 4
    # a_n_a_nplus1 = slide_strand(start_index=n, n_slide=2)
    # assert a_n_a_nplus1 * a(n) == a(n + 1) * a_n_a_nplus1

    # Check 2.1 Lemma from Garside
    # The Braid group and other groups
    # https://webhomes.maths.ed.ac.uk/~v1ranick/papers/garside.pdf
    # Note this can be viewed ad an extension of Artin relationship 2
    t = 4
    s = 2
    pi_t = slide_strand(start_index=1, n_slide=t)

    assert a(s) * pi_t == pi_t * a(s - 1)


def test_half_twist_braid():
    b = Braid((), 5)
    b = b.half_twist(sign=1)
    assert b.perm() == [5, 4, 3, 2, 1]

    b_cat = garside_half_twist_braid(5)
    assert b == b_cat

    # Check default
    bd = Braid((), 5)
    bd = bd.half_twist()
    assert b.word_eq(bd)

    # Check only sign is taken
    b2 = Braid((), 5)
    b2 = b2.half_twist(sign=2)
    assert b.word_eq(b2)

    # Check negative sign
    b = Braid((), 5)
    b = b.half_twist(sign=-1)
    assert b.perm() == [5, 4, 3, 2, 1]

    # Check that Garside half twist is pseudocommuting with each generator
    n = 6
    for i in range(1, n):
        b = Braid((), 6)
        assert (b.half_twist() * a(i)) == (a(n - i) * b.half_twist())


def test_full_twist_braid():
    """
    Check that full twist (one turn) is commutting with all braid
    σi∆n² = ∆n.σn−i.∆n = ∆nσn−(n−i) = ∆n²σi.
    https://perso.eleves.ens-rennes.fr/people/baptiste.dugue/M%C3%A9moire_Stage_Tresses.pdf
    page 9
    """
    # Random braid
    b = Braid((1, 2, 3, 2, 3, 1, -4), 5)

    assert b * full_twist_braid(5) == full_twist_braid(5) * b


def _drawn(make):
    """A catalogued braid, drawn as it is made: a braid, and how many times
    to repeat it."""
    braid, repeat = make()
    assert isinstance(braid, Braid) and braid.generators
    assert isinstance(repeat, int) and repeat > 0


def test_flat3():
    _drawn(flat3)


def test_inverted_flat3():
    _drawn(inverted_flat3)


def test_weave3():
    _drawn(weave3)


def test_square4():
    """


    Returns:

    """
    _drawn(square4)


def test_flat4():
    """

    Returns:

    """
    b, _ = asymmetric_flat4()
    assert b.is_periodic()


def test_abok_2934():
    _drawn(abok_2974)


def test_flat5():
    _drawn(flat5)


def test_flat6():
    """

    Returns:

    """
    _drawn(flat6)


def test_regular_flat_braid_6():
    """

    Returns:

    """
    _drawn(regular_flat6)


def test_double_flat3():
    _drawn(double_flat3)


def test_double_flat3_does_not_pass_off_2971_as_its_parallel_twin():
    """ABOK 2972, the parallel double flat sinnet, is not made yet: asked
    for, it says so, rather than give 2971 again."""
    with pytest.raises(NotImplementedError):
        double_flat3(parallel=True, draw=False)


def test_the_catalogue_s_braids_are_words_to_try(monkeypatch):
    """Each catalogued braid, as the word it repeats, built without drawing:
    repeated as often as the example says, every strand comes home."""
    import braidpy.braid_catalog as catalog
    from braidpy.braid_catalog import CATALOGUE, word_examples
    from braidpy.braidword import parse_word
    from braidpy.pure_braid import is_pure

    def no_drawing(*args, **kwargs):
        raise AssertionError("drawn")

    monkeypatch.setattr(Braid, "draw", no_drawing)
    examples = word_examples()
    assert len(examples) == len(CATALOGUE) + len(catalog.WORD_EXAMPLES)
    for example, name in zip(examples, CATALOGUE):
        braid, _ = getattr(catalog, name)(draw=False)
        unit = parse_word(example["word"])
        times, rest = divmod(len(braid.generators), len(unit))
        assert rest == 0 and tuple(unit * times) == tuple(braid.generators), name
        repeated = Braid(tuple(unit * example["repeat"]), example["n_strands"])
        assert is_pure(repeated), name
        assert len(repeated.generators) >= 12, name


def test_the_rectangular_braid_of_14_runs_on_two_tracks_of_seven():
    """Its two sets of seven places never mix, and they interleave in pairs.

    The permutation of one repeat is two 7-cycles, so seven repeats bring
    every strand home; labelling each place by its cycle and reading across
    the face gives ABBAABBAABBAAB.  That is a property of the word, not of
    any arrangement behind it.  As many crossings go one way as the other,
    so nothing twists.
    """
    from braidpy.braid_catalog import rectangular14
    from braidpy.pure_braid import closing_repeats, cycles, is_pure, repeating_unit

    braid, home = rectangular14(draw=False)
    assert braid.n_strands == 14
    assert len(braid.generators) == 32
    assert repeating_unit(list(braid.generators)) == list(braid.generators)
    assert sum(1 if g > 0 else -1 for g in braid.generators) == 0
    assert home == 7 == closing_repeats(braid, limit=None)
    orbits = cycles(braid)
    assert sorted(len(orbit) for orbit in orbits) == [7, 7]
    track = {place: number for number, orbit in enumerate(orbits) for place in orbit}
    assert [track[place] for place in range(14)] == [0, 1, 1, 0] * 3 + [0, 1]
    assert is_pure(Braid(tuple(braid.generators) * home, 14))


def test_the_rectangular_braid_of_20_is_not_a_wider_copy_of_the_14():
    """Two sets of ten this time, and they interleave unevenly.

    Forty-six crossings a repeat over all nineteen places, as many one way
    as the other; ten repeats bring every strand home.  Labelling each place
    by its cycle gives ABBABAABABBABAABABBA, in threes and pairs where the
    braid of fourteen is in pairs throughout.
    """
    from braidpy.braid_catalog import rectangular20
    from braidpy.pure_braid import closing_repeats, cycles, is_pure, repeating_unit

    braid, home = rectangular20(draw=False)
    assert braid.n_strands == 20
    assert len(braid.generators) == 46
    assert len({abs(g) for g in braid.generators}) == 19
    assert repeating_unit(list(braid.generators)) == list(braid.generators)
    assert sum(1 if g > 0 else -1 for g in braid.generators) == 0
    assert home == 10 == closing_repeats(braid, limit=None)
    orbits = cycles(braid)
    assert sorted(len(orbit) for orbit in orbits) == [10, 10]
    track = {place: number for number, orbit in enumerate(orbits) for place in orbit}
    assert "".join("AB"[track[place]] for place in range(20)) == "ABBABAABABBABAABABBA"
    assert is_pure(Braid(tuple(braid.generators) * home, 20))
