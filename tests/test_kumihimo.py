# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The Kumihimo disk: S and R moves, and the braid word they make.

:class:`~braidpy.kumihimo.Kumihimo` keeps two accounts of the same thing — the
order the strands are in, and the braid word that got them there — and the
account that matters is that those two agree.  A word that does not permute
the strands the way the disk did is not the word of that braid, however
plausible it looks.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

from braidpy.kumihimo import Kumihimo  # noqa: E402


def permutation_of(word, n_strands):
    """Where a braid word sends each position, applied left to right."""
    order = list(range(n_strands))
    for generator in word:
        low = abs(generator) - 1
        order[low], order[low + 1] = order[low + 1], order[low]
    return order


# ── The invariant the class exists to maintain ────────────────────────────────


@pytest.mark.parametrize("pattern", ["S", "R", "SR", "SRSR", "SSRR", "RSRSRS"])
@pytest.mark.parametrize("n_strands", [8, 12])
def test_the_word_permutes_the_strands_the_way_the_disk_did(pattern, n_strands):
    """The braid word and the tracked order must tell the same story.

    This is the whole of the class's correctness: everything else is drawing.
    """
    disk = Kumihimo(n_strands).move(pattern)
    assert disk.state == permutation_of(disk.braid_word, n_strands)


def test_a_swap_moves_exactly_two_strands():
    """S exchanges top and bottom and leaves everyone else alone."""
    disk = Kumihimo(8).move("S")
    assert disk.state[0] == 4 and disk.state[4] == 0
    assert disk.state[1:4] == [1, 2, 3]
    assert disk.state[5:] == [5, 6, 7]


def test_a_swap_crosses_everyone_in_between_and_unwinds_again():
    """Top and bottom are not neighbours, so the swap is a path, not a σ.

    Reaching across ``m`` strands costs ``m`` crossings out and ``m - 1``
    back: the far strand is carried over, the near ones are put back.
    """
    disk = Kumihimo(8).move("S")
    assert disk.braid_word == [1, 2, 3, 4, -3, -2, -1]


def test_four_quarter_turns_bring_the_disk_home():
    """R is a quarter turn, so four of them are the identity on the order."""
    disk = Kumihimo(8).move("RRRR")
    assert disk.state == list(range(8))
    assert disk.state == permutation_of(disk.braid_word, 8)


def test_a_rotation_is_not_free():
    """Turning the disk crosses strands, and the word says so.

    Worth stating because it is the cost of writing a *ring* as a flat braid
    word: a quarter turn of an eight-strand disk is two whole cycles of
    generators, where a word on an annulus would call it a turn.
    """
    disk = Kumihimo(8).move("R")
    assert len(disk.braid_word) == 14
    assert disk.state == permutation_of(disk.braid_word, 8)


# ── Bookkeeping ───────────────────────────────────────────────────────────────


def test_the_history_and_the_frames_keep_step_with_the_moves():
    disk = Kumihimo(8).move("SRSR")
    assert disk.history == ["S", "R**1", "S", "R**1"]
    assert len(disk.frames) == len(disk.history) + 1
    assert disk.frames[0] == list(range(8))
    assert disk.frames[-1] == disk.state
    assert disk.pattern == "SRSR"


def test_the_word_is_signed_integers_like_the_rest_of_braidpy():
    """So it can be handed to Braid without translation."""
    disk = Kumihimo(8).move("SR")
    assert disk.braid_word
    assert all(isinstance(generator, int) for generator in disk.braid_word)
    assert all(1 <= abs(generator) <= 7 for generator in disk.braid_word)


def test_the_word_a_disk_makes_is_a_braid_braidpy_understands():
    """The point of producing a word at all: the rest of the library takes it."""
    from braidpy.braid import Braid

    disk = Kumihimo(8).move("SRSR")
    braid = Braid(tuple(disk.braid_word), n_strands=8)
    assert braid.format()


# ── What it refuses ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("n_strands", [5, 6, 7, 9, 10])
def test_a_disk_that_is_not_a_quarter_of_a_whole_number_is_refused(n_strands):
    """The moves are quarter turns, so the slot count has to divide by four."""
    with pytest.raises(ValueError, match="divisible by 4"):
        Kumihimo(n_strands)


def test_an_unknown_move_is_refused():
    with pytest.raises(ValueError, match="Invalid step"):
        Kumihimo(8).move("SRX")


def test_the_timeline_draws(tmp_path):
    """Drawing is not correctness, but it should not raise."""
    import matplotlib.pyplot as plt

    Kumihimo(8).move("SRSR").plot_timeline()
    plt.close("all")
