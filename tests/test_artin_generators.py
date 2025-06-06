from sympy.testing import pytest

from braidpy import Braid
from braidpy.artin_generators import a


def test_init():
    assert a(0).word_eq(Braid(0))
    assert a(1).word_eq(Braid(1))
    assert a(-1).word_eq(Braid(-1))
    assert a(-3).word_eq(Braid(-3))
    with pytest.raises(ValueError):
        a([-2, 1])


def test_a():
    """Test short notation with artin generator as derived class of Braid"""
    print(a(1))
    assert a(1) == Braid([1])

    assert a(1) ** (-2) == Braid([-1, -1])


def test_n():
    # Check we can change the number of strands in a compact notation
    assert (a(2) * a(1) ** (-2)).n(3) == Braid([2, -1, -1], 3)


def test_mixing_operation_with_braid():
    # Check we can change the number of strands in a compact notation
    assert a(2) * Braid([1, 5]) == Braid([2, 1, 5])
    assert Braid([1, 5]) * a(2) == Braid([1, 5, 2])
