# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braid words for the web page, flat or round a ring."""

import pytest
from web_checks import check

from braidpy.web import build, parse_word


def test_a_word():
    result = build({"source": "word", "word": "1 -2", "repeat": 3, "iterations": 20})
    check(result, 3)
    assert result["info"]["word"] == "1 -2 1 -2 1 -2"
    assert (
        result["info"]["permutation"] == [2, 3, 1]
        or len(result["info"]["permutation"]) == 3
    )


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"source": "word", "word": ""}, "Give a braid word"),
        ({"source": "word", "word": "3", "n_strands": 3}, "at least 4"),
        ({"source": "word", "word": "1", "repeat": 500}, "between"),
    ],
)
def test_what_cannot_be_made_is_explained(spec, message):
    with pytest.raises(ValueError, match=message):
        build(spec)


@pytest.mark.parametrize(
    "word, n_strands",
    [("1", 2), ("1 2 3", 4), ("1 -2", 3), ("7 6 5 4 4 3 2 1 7 6 5 4 3 2 1", 8)],
)
def test_a_word_to_settle_by_physics_is_laid_round_a_ring(word, n_strands):
    """Settled by physics, a word is laid round a ring as a disk braid is,
    every crossing kept as two neighbours swapping places — none rolled
    into a turn of the bobbins, which on a disk crosses nothing: read back
    round the ring, it is the word, its twist and all."""
    from braidpy.annulus_braid import solid_word
    from braidpy.take_off import disk_annular_word
    from braidpy.web.words import _ring_program, _ring_steps

    flat = parse_word(word) * 3
    program = _ring_program(flat, n_strands, False)
    start, steps = _ring_steps(program)
    annular, n = disk_annular_word(start, steps, program["n_slots"], clockwise=True)
    assert list(solid_word(annular, n)) == flat

    spec = {"source": "word", "word": word, "n_strands": n_strands, "repeat": 3}
    laid = build({**spec, "settle": "physics"}, tighten=False)
    row = build(spec, tighten=False)
    assert laid["timeline"]["kind"] == "disk"
    assert row["timeline"]["kind"] == "line"
    # The same braid, made the same way on a marudai.
    assert laid["info"]["word"] == row["info"]["word"]
    assert [s["name"] for s in laid["strands"]] == [s["name"] for s in row["strands"]]
    assert laid["disk"] == row["disk"]


def test_a_word_comes_with_its_moves_on_a_ring():
    result = build(
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 4}, tighten=False
    )
    disk = result["disk"]
    # Hanging free, as a disk braid does; held only while the bobbins turn.
    assert disk["held"] is False
    assert disk["twists"] is True
    assert sorted(disk["start"]) == sorted(set(disk["start"]))
    assert len(disk["start"]) == 3
    # Each crossing a swap in three moves: there is no turn in a plait.
    assert len(disk["steps"]) == 8


def test_a_ring_word_is_made_as_its_moves_round_the_ring():
    """A ring word is read with the strands round a circle: 1 to n - 1 cross
    neighbours as in a braid word, n crosses the last strand and the first,
    across the seam, and n + 1 turns every strand one place round.  It is
    made move by move as written, and is the braid its flat word is."""
    from braidpy.annulus_braid import solid_word

    spec = {"source": "word", "layout": "ring", "word": "1 3 -2", "n_strands": 3}
    result = build({**spec, "repeat": 2}, tighten=False)
    moves = [1, 3, -2] * 2
    assert result["info"]["annular_word"] == "1 3 -2 1 3 -2"
    assert result["info"]["word"] == " ".join(map(str, solid_word(moves, 3)))
    assert result["title"].startswith("Ring word")
    # Each crossing is a swap in three moves, the seam's as any other.
    steps = result["disk"]["steps"]
    assert len(steps) == len(moves)
    assert all(len(step) == 3 for step in steps)


def test_a_ring_word_turns_the_bobbins():
    result = build(
        {"source": "word", "layout": "ring", "word": "4", "n_strands": 3, "repeat": 3},
        tighten=False,
    )
    steps = result["disk"]["steps"]
    assert len(steps) == 3
    assert all(len(step) == 3 for step in steps)
    assert result["info"]["word"] == "2 1 2 1 2 1"


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"word": "5", "n_strands": 3}, "up to 4"),
        ({"word": "1 -1", "n_strands": 3}, "crosses nothing"),
    ],
)
def test_a_ring_word_that_cannot_be_made_says_so(spec, message):
    with pytest.raises(ValueError, match=message):
        build({"source": "word", "layout": "ring", **spec}, tighten=False)


@pytest.mark.parametrize(
    "word, n_strands, repeats",
    [("1 -2", 3, 3), ("1 1", 2, 1), ("1", 2, 2), ("1 3", 4, 2), ("1 2 4", 5, 6)],
)
def test_a_braid_says_how_many_times_to_repeat_it_to_be_pure(word, n_strands, repeats):
    """Repeated as many times as its permutation's order, every strand is
    back where it started: the braid is pure."""
    from braidpy.braid import Braid

    info = build(
        {"source": "word", "word": word, "n_strands": n_strands}, tighten=False
    )["info"]
    assert info["pure_after"] == repeats
    assert Braid(parse_word(word) * repeats, n_strands).is_pure()


@pytest.mark.parametrize(
    "spec",
    [
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6},
        {"source": "word", "layout": "ring", "word": "1 3", "n_strands": 3},
    ],
)
def test_how_many_repeats_make_it_pure_counts_its_unit(spec):
    """The repeats asked for are the braid's word, or its moves' cycle: so
    many of them, and no fewer, make a pure braid, whatever was made."""
    unit = build({**spec, "repeat": 1, "cycles": 1}, tighten=False)["info"]
    info = build(spec, tighten=False)["info"]
    assert info["pure_after"] == unit["pure_after"]
    assert info["repeated"] == ("cycle" if "cycles" in spec else "repeat")
    k = unit["pure_after"]
    again = build({**spec, "repeat": k, "cycles": k}, tighten=False)["info"]
    assert again["pure"]
    if k > 1:
        fewer = build({**spec, "repeat": k - 1, "cycles": k - 1}, tighten=False)
        assert not fewer["info"]["pure"]


@pytest.mark.parametrize(
    "spec, made",
    [
        ({"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 4}, 4),
    ],
)
def test_a_braid_says_how_many_repeats_were_made(spec, made):
    """Beside how many repeats make it pure, how many were made — and so
    whether what was made is."""
    info = build(spec, tighten=False)["info"]
    assert info.get("made") == made
    if made:
        assert info["pure"] == (made % info["pure_after"] == 0)


def test_a_long_word_is_cut_short_in_the_title():
    word = " ".join(["1 -2"] * 30)
    title = build({"source": "word", "word": word, "n_strands": 3}, tighten=False)[
        "title"
    ]
    assert title.startswith("Braid word 1 -2 1 -2")
    assert title.endswith("…")
    assert len(title) < 50
