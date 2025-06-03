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
