# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids in band generators: braidpy.band_canonical_form."""

import random

import pytest

from braidpy import Braid
from braidpy.band_canonical_form import (
    _blocks,
    _compose,
    _delta,
    _from_blocks,
    _transposition,
    artin_from_band,
    band_left_normal_form,
    band_word,
    factor_blocks,
)


def _math_braid_form(word, n):
    """math-braid's band normal form, as turns and blocks: the check."""
    import math_braid

    made = math_braid.Braid(list(word), n)
    made.cleanUpFactors()
    factors = []
    for factor in made.a:
        groups: dict[int, list[int]] = {}
        for strand, label in enumerate(factor.d_cycles):
            groups.setdefault(label, []).append(strand + 1)
        factors.append(sorted(tuple(b) for b in groups.values() if len(b) > 1))
    return made.p, factors


def test_the_normal_form_is_math_braid_s():
    """The same turns and the same blocks, factor by factor, as math-braid
    gives, on random words."""
    rng = random.Random(0)
    for _ in range(400):
        n = rng.randint(2, 7)
        word = [
            rng.choice((-1, 1)) * rng.randint(1, n - 1)
            for _ in range(rng.randint(1, 20))
        ]
        p, factors = band_left_normal_form(word, n)
        assert (p, [sorted(factor_blocks(f)) for f in factors]) == _math_braid_form(
            word, n
        )


def test_a_factor_is_its_blocks_each_a_descending_cycle():
    """Built from its band letters, highest strand first, a block is its
    strands each a place up it."""
    n = 6
    made = tuple(range(n))
    for t, s in ((5, 3), (3, 1)):  # a_53 a_31, strands from 0
        made = _compose(made, _transposition(n, t, s))
    assert made == _from_blocks(n, [[1, 3, 5]])
    assert _blocks(_delta(n)) == [list(range(n))]


def test_a_band_word_reads_back_as_the_braid():
    rng = random.Random(1)
    for _ in range(100):
        n = rng.randint(2, 6)
        word = [rng.choice((-1, 1)) * rng.randint(1, n - 1) for _ in range(12)]
        letters = band_word(word, n)
        assert Braid(tuple(artin_from_band(letters)), n) == Braid(tuple(word), n)


def test_one_band_letter_crosses_two_strands_in_front_of_the_rest():
    assert artin_from_band([(2, 1)]) == [1]
    assert artin_from_band([(4, 1)]) == [3, 2, 1, -2, -3]
    assert artin_from_band([(1, 4)]) == [3, 2, -1, -2, -3]
    with pytest.raises(ValueError):
        artin_from_band([(2, 2)])


def test_equal_braids_have_one_band_form():
    a, b = Braid((1, 2, 1), 3), Braid((2, 1, 2), 3)
    assert a.get_band_canonical_factors() == b.get_band_canonical_factors()
    assert a.band_word() == b.band_word()


def test_a_full_twist_is_n_turns():
    for n in (2, 3, 5):
        full = Braid([1, -1], n_strands=n).full_twist()
        f = full.get_band_canonical_factors()
        assert (f.n_half_twist, f.Ai) == (n, ())


def test_a_disk_braid_is_shorter_in_band_letters():
    """Kongo gumi on 8 strands: its strands cross the disk, each crossing a
    band letter where it is a run of crossings of neighbours."""
    from braidpy.making import _unit
    from braidpy.web import build

    info = build(
        {"source": "mobidai", "name": "KONGO_8", "iterations": 0}, tighten=False
    )
    unit, _ = _unit(info["info"])
    unit = unit.shortened()
    assert len(unit.band_word()) < len(unit.generators) / 1.5


def test_a_band_word_typed_is_read_back():
    from braidpy.band_canonical_form import band_text
    from braidpy.braidword import parse_band_word

    letters = band_word([1, -2, 3, 1], 4)
    assert parse_band_word(band_text(letters)) == letters
    assert parse_band_word("4:1, 1:3") == [(4, 1), (1, 3)]
    for bad in ("4-1", "2:2", "0:3"):
        with pytest.raises(ValueError):
            parse_band_word(bad)


def test_braid_studio_shows_a_band_word_where_it_is_shorter():
    """A disk braid's card says its band word, and makes it again as the
    same braid; a plait's, of neighbours crossing, does not."""
    from braidpy.web import build

    disk = build(
        {"source": "mobidai", "name": "KONGO_8", "iterations": 0},
        tighten=False,
    )["info"]
    assert "band_word" in disk
    made = build(
        {
            "source": "word",
            "layout": "band",
            "word": disk["band_word"],
            "n_strands": disk["n_strands"],
            "iterations": 0,
        },
        tighten=False,
    )
    word = tuple(int(g) for g in disk["word"].split())
    again = tuple(int(g) for g in made["info"]["word"].split())
    n = disk["n_strands"]
    assert Braid(again, n) == Braid(word, n)
    assert made["title"].startswith("Band word ")
    plait = build(
        {"source": "word", "word": "1 -2", "repeat": 3, "iterations": 0},
        tighten=False,
    )["info"]
    assert "band_word" not in plait


def test_a_word_is_read_as_band_letters_as_it_stands():
    """Each run spelling a band letter one letter, every other crossing a
    letter of neighbours: never longer, the same braid."""
    from braidpy.band_canonical_form import band_letters

    assert band_letters([3, 2, -1, -2, -3, 1]) == [(1, 4), (2, 1)]
    assert band_letters([1, -2]) == [(2, 1), (2, 3)]
    rng = random.Random(2)
    for _ in range(200):
        n = rng.randint(2, 6)
        word = [rng.choice((-1, 1)) * rng.randint(1, n - 1) for _ in range(15)]
        word += artin_from_band([(n, 1)])
        letters = band_letters(word)
        assert len(letters) <= len(word)
        assert Braid(tuple(artin_from_band(letters)), n) == Braid(tuple(word), n)
