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


@pytest.mark.parametrize(
    "text, word",
    [
        ("1 -2 1", [1, -2, 1]),
        ("1,-2, 1", [1, -2, 1]),
        ("s1 s2^-1 s1", [1, -2, 1]),
        ("σ1 σ2^(-1)", [1, -2]),
        ("aBa", [1, -2, 1]),
        ("  ", []),
    ],
)
def test_words_are_read_in_every_usual_spelling(text, word):
    from braidpy.braidword import parse_word

    assert parse_word(text) == word


@pytest.mark.parametrize("text", ["1 x 2", "0 1", "s1 s"])
def test_a_word_that_cannot_be_read_says_so(text):
    from braidpy.braidword import parse_word

    with pytest.raises(ValueError):
        parse_word(text)
