from braidpy.braid import Braid, slide_strand
from braidpy.artin_generators import a
from braidpy.braid_catalog import (
    full_twist_braid,
    flat3,
    inverted_flat3,
    square4,
    asymmetric_flat4,
    flat6,
    flat5,
    regular_flat6,
    garside_half_twist_braid,
    double_flat3,
    abok_2974,
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
    Chech that full twist (one turn) is commutting with all braid
    σi∆n² = ∆n.σn−i.∆n = ∆nσn−(n−i) = ∆n²σi.
    https://perso.eleves.ens-rennes.fr/people/baptiste.dugue/M%C3%A9moire_Stage_Tresses.pdf
    page 9
    """
    # Random braid
    b = Braid((1, 2, 3, 2, 3, 1, -4), 5)

    assert b * full_twist_braid(5) == full_twist_braid(5) * b


def test_flat3():
    b, n = flat3()


def test_inverted_flat3():
    b, n = inverted_flat3()


def test_weave3():
    b, n = weave3()


def test_square4():
    """


    Returns:

    """
    b, n = square4()


def test_flat4():
    """

    Returns:

    """
    b, n = asymmetric_flat4()
    assert b.is_periodic()


def test_abok_2934():
    b, n = abok_2974()


def test_flat5():
    b, n = flat5()


def test_flat6():
    """

    Returns:

    """
    b, n = flat6()


def test_regular_flat_braid_6():
    """

    Returns:

    """
    b, n = regular_flat6()


def test_double_flat3():
    b, n = double_flat3()


def test_the_catalogue_s_braids_are_words_to_try(monkeypatch):
    """Each catalogued braid, as the word it repeats, built without drawing:
    repeated as often as the example says, every strand comes home."""
    import braidpy.braid_catalog as catalog
    from braidpy.braid_catalog import CRAFT_BRAIDS, word_examples
    from braidpy.braidword import parse_word
    from braidpy.pure_braid import is_pure

    def no_drawing(*args, **kwargs):
        raise AssertionError("drawn")

    monkeypatch.setattr(Braid, "draw", no_drawing)
    examples = word_examples()
    assert len(examples) == len(CRAFT_BRAIDS) + len(catalog.WORD_EXAMPLES)
    for example, name in zip(examples, CRAFT_BRAIDS):
        braid, _ = getattr(catalog, name)(draw=False)
        unit = parse_word(example["word"])
        times, rest = divmod(len(braid.generators), len(unit))
        assert rest == 0 and tuple(unit * times) == tuple(braid.generators), name
        repeated = Braid(tuple(unit * example["repeat"]), example["n_strands"])
        assert is_pure(repeated), name
        assert len(repeated.generators) >= 12, name
