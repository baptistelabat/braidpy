from braidpy.braid import Braid, slide_strand
from braidpy.artin_generator import a
from braidpy.braid_catalog import full_twist_braid


def test_slide_strand():
    b = slide_strand(start_index=1, n_slide=2, sign=1)
    b.draw()
    assert b.perm() == [2, 3, 1]

    b = slide_strand(start_index=1, n_slide=2, sign=-1)
    b.draw()
    assert b.perm() == [2, 3, 1]

    # Check n_slide=1 slide corresponds to Artin's generator
    n = 3
    b = slide_strand(start_index=n, n_slide=1, sign=1)

    b.draw()
    a(n, n + 1).draw()
    assert b.word_eq(a(n, n + 1))

    # Check the artin relationship 2
    n = 4
    a_n_a_nplus1 = slide_strand(start_index=n, n_slide=2, sign=1)
    assert a_n_a_nplus1 * a(n) == a(n + 1) * a_n_a_nplus1


def test_half_twist_braid():
    b = Braid((), 5)
    b = b.half_twist(sign=1)
    assert b.perm() == [5, 4, 3, 2, 1]

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
