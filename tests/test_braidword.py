import pytest

from braidpy.braidword import braidword_alpha_to_numeric


def test_braidword_alpha_to_numeric():
    word = "abAB"
    assert braidword_alpha_to_numeric(word) == [1, 2, -1, -2]

    word = ""
    assert braidword_alpha_to_numeric(word) == []

    word = "aB1"
    with pytest.raises(ValueError):
        braidword_alpha_to_numeric(word)

    word = "#A"
    assert braidword_alpha_to_numeric(word) == [0, -1]
