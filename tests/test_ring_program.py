# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid as neighbours swapping places round a ring: braidpy.ring_program,
the step between a braid and the ways of making it."""

import pytest

from braidpy import Braid
from braidpy.braid_catalog import word_examples
from braidpy.ring_program import RingProgram, Swap, from_braid, same_braid


def _words():
    for example in word_examples():
        if example.get("layout") == "ring":
            continue
        word = tuple(int(g) for g in example["word"].split()) * example["repeat"]
        yield example["title"], Braid(word, example["n_strands"])


@pytest.mark.parametrize("extra", [0, 3])
def test_every_catalogue_word_comes_back_exactly(extra):
    """Made into a ring program and read back off its disk moves, with or
    without empty places round the ring: the very braid, its crossings in
    another order only where they commute."""
    for title, braid in _words():
        program = from_braid(braid, braid.n_strands + extra)
        assert program.braid() == braid, title


def test_a_crossing_s_sign_is_who_is_lifted():
    """The strand on the right lifted over the one on its left is σᵢ."""
    right_over = RingProgram(3, (0, 1, 2), ((Swap(1, 1),),))
    left_over = RingProgram(3, (0, 1, 2), ((Swap(1, -1),),))
    assert list(right_over.braid().generators) == [2]
    assert list(left_over.braid().generators) == [-2]


def test_swaps_of_a_row_share_no_place_and_keep_each_place_s_order():
    braid = Braid((1, 3, -2, 1, 3, 2), 4)
    program = from_braid(braid)
    for row in program.rows:
        places = [p for swap in row for p in (swap.place, swap.place + 1)]
        assert len(places) == len(set(places))
    # σ1 and σ3 commute and share a row; -σ2 waits for both.
    assert [len(row) for row in program.rows] == [2, 1, 2, 1]
    assert program.braid() == braid


def test_a_strand_into_an_empty_place_crosses_nothing():
    program = RingProgram(4, (0, 1, None, None), ((Swap(1, 1),), (Swap(0, -1),)))
    assert program.ends() == (None, 0, 1, None)
    assert list(program.braid().generators) == []


def test_strands_carried_once_round_the_ring_twist_the_braid_once():
    """Every strand walked across the seam and back where it started, by
    empty places: a full twist, as a tubular machine's carriers twist the
    braid going round."""
    places = 5
    held = [0, 1, 2, None, None]
    swaps = []
    for _ in range(places):
        # The front strand first, so each steps into an empty place.
        for p in sorted(
            (p for p, k in enumerate(held) if k is not None),
            key=lambda p: (p - held.index(0)) % places,
            reverse=True,
        ):
            q = (p + 1) % places
            swaps.append((Swap(p, 1),))
            held[p], held[q] = held[q], held[p]
    program = RingProgram(places, (0, 1, 2, None, None), tuple(swaps))
    assert program.ends() == (0, 1, 2, None, None)
    full_twist = Braid((1, 2) * 3, 3)
    assert same_braid(program.braid(), full_twist)
    assert not same_braid(program.braid(), Braid((), 3))


def test_strands_must_stay_clear_of_the_seam():
    with pytest.raises(ValueError, match="seam"):
        from_braid(Braid((1, 2), 3), n_places=4, offset=2)


@pytest.mark.parametrize(
    "start, rows, wrong",
    [
        ((0, 0, 1), (), "each once"),
        ((0, 1), (), "for a ring of 3"),
        ((0, 1, 2), ((Swap(3, 1),),), "no place"),
        ((0, 1, 2), ((Swap(0, 0),),), "sign"),
        ((0, 1, 2), ((Swap(0, 1), Swap(1, 1)),), "share a place"),
    ],
)
def test_a_program_that_cannot_be_made_is_refused(start, rows, wrong):
    with pytest.raises(ValueError, match=wrong):
        RingProgram(3, start, rows)


def test_the_same_braid_is_the_same_topology():
    """Read from another strand, or written otherwise: the same braid."""
    plait = Braid((1, -2) * 3, 3)
    assert same_braid(plait, Braid((-2, 1) * 3, 3))
    assert not same_braid(plait, Braid((1, 2) * 3, 3))
