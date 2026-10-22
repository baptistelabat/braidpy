# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as moves on a kumihimo disk: braidpy.bridges.disk, read back as
braidpy reads any mobidai."""

import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.bridges.disk import disk_braid, disk_moves


def _words():
    for example in word_examples():
        if example.get("layout") == "ring":
            continue
        word = tuple(int(g) for g in example["word"].split()) * example["repeat"]
        yield example["title"], Braid(word, example["n_strands"])


def test_every_catalogue_word_is_made_on_the_disk():
    for title, braid in _words():
        assert disk_braid(disk_moves(braid)) == braid, title


def test_a_crossing_is_three_moves_and_only_the_first_crosses():
    """σ₁ on three strands, two slots apart from slot 3: the right strand
    over the left into slot 2, the left into slot 5, the right into 3."""
    moves = disk_moves(Braid((1,), 3))
    assert moves.slots == (3, 5, 7)
    assert moves.moves == ((5, 2), (3, 5), (2, 3))
    assert moves.text() == "5>2, 3>5, 2>3"
    assert disk_braid(moves) == Braid((1,), 3)
    left_over = disk_moves(Braid((-1,), 3))
    assert left_over.moves == ((3, 6), (5, 3), (6, 5))
    assert disk_braid(left_over) == Braid((-1,), 3)


def test_braid_studio_makes_the_disk_s_moves():
    from braidpy.web import build

    plait = Braid((1, -2) * 3, 3)
    made = build({**disk_moves(plait).spec(), "iterations": 0}, tighten=False)
    assert Braid(tuple(int(g) for g in made["info"]["word"].split()), 3) == plait


def test_a_disk_too_small_is_refused():
    with pytest.raises(ValueError, match="34 slots"):
        disk_moves(Braid((1,) * 3, 16))
