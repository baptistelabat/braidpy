from braidpy.ashley_solid_sinnet import (
    init_spaces_from_counts,
    flatten_spaces,
    ashley_single_move_to_artin,
    ashley_to_artin_exact,
)


def test_init_spaces_from_counts():
    spaces = init_spaces_from_counts(counts=[2, 1, 1, 2, 1, 1])
    assert spaces == {1: [1, 2], 2: [3], 3: [4], 4: [5, 6], 5: [7], 6: [8]}


def test_flatten_spaces():
    flat = flatten_spaces(spaces={1: [1, 2], 2: [3], 3: [4], 4: [5, 6], 5: [7], 6: [8]})
    assert flat == [1, 2, 3, 4, 5, 6, 7, 8]


def test_ashley_single_move_to_artin_step1():
    counts_3042 = [2, 1, 1, 2, 1, 1]

    counts, word = ashley_single_move_to_artin(
        counts=counts_3042, from_space=1, to_space=5
    )
    assert word == [-2, -3, -4, -5]
    assert counts == [1, 1, 1, 2, 2, 1]


def test_ashley_single_move_to_artin_step2():
    counts_3042_step_2 = [1, 1, 1, 2, 2, 1]

    counts, word = ashley_single_move_to_artin(
        counts=counts_3042_step_2, from_space=2, to_space=4
    )
    assert word == [1, -1, -2, -3, -4, -5, -6, -7, 7, 6, 5]
    assert counts == [1, 0, 1, 3, 2, 1]


def test_ashley_single_move_to_artin_step3():
    counts_3042_step_3 = [1, 0, 1, 3, 2, 1]

    counts, word = ashley_single_move_to_artin(
        counts=counts_3042_step_3, from_space=3, to_space=1
    )
    assert word == [-2, -3, -4, -5, -6, -7, 7, 6, 5, 4, 3, 2, 1]
    assert counts == [2, 0, 0, 3, 2, 1]


def test_ashley_to_artin_exact():
    counts_3042 = [2, 1, 1, 2, 1, 1]
    moves_3042 = {1: 5, 4: 2, 5: 3, 2: 6, 3: 1, 6: 4}

    counts, word = ashley_to_artin_exact(counts_3042, moves_3042)
    assert counts == counts_3042  # Complete cycle
    assert word == [
        -2,
        -3,
        -4,
        -5,
        3,
        -7,
        7,
        6,
        5,
        4,
        3,
        2,
        1,
        -1,
        -2,
        -3,
        1,
        -1,
        -2,
        -3,
        -4,
        -5,
        -6,
        -7,
        -4,
        -5,
        -6,
        -7,
        7,
        6,
        5,
        4,
        3,
        2,
        1,
        6,
    ]


# ---------------------------------------------------------------- on a disk

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from braidpy import Braid  # noqa: E402
from braidpy.ashley_solid_sinnet import AshleySolidSinnet, sinnet_disk  # noqa: E402
from braidpy.take_off import (  # noqa: E402
    disk_annular_word,
    disk_crossing_steps,
    mobidai_steps,
)


def _catalogue():
    import braidpy.solid_sinnets_catalog as catalogue

    return {
        name: value
        for name, value in vars(catalogue).items()
        if isinstance(value, AshleySolidSinnet)
    }


def _cycles(permutation):
    seen, lengths = set(), []
    for i in range(len(permutation)):
        length = 0
        while i not in seen:
            seen.add(i)
            i = permutation[i]
            length += 1
        if length:
            lengths.append(length)
    return sorted(lengths)


def _end(disk):
    where = dict(disk.start)
    for step in disk.steps:
        for k, delta in step.items():
            where[k] = (where[k] - 1 + delta) % disk.n_slots + 1
    return where


def test_a_move_takes_the_earliest_strand_over_all_it_passes():
    from braidpy.solid_sinnets_catalog import abok_3042

    disk = sinnet_disk(abok_3042)
    order, crossings, _ = disk_crossing_steps(disk.start, disk.steps, disk.n_slots)
    # 1 → 5: space 1's right-hand strand, 2, anticlockwise over the four
    # strands of spaces 2, 3 and 4, into the near end of space 5.
    assert disk.labels[0] == "1 → 5"
    assert disk.steps[0] == {2: 14}
    assert crossings[:4] == [(2, 3), (2, 4), (2, 5), (2, 6)]
    # 4 → 2: space 4's left-hand strand, clockwise over space 3's, into the
    # near end of space 2, crossing none of its strands.
    assert disk.labels[2] == "4 → 2"
    assert crossings[4] == (5, 4)
    # Every strand moved crosses those it passes; strands settling, nobody.
    # 5 → 3 passes spaces 6, 1 and 2 (now holding two), 2 → 6 space 1,
    # 3 → 1 spaces 4, 5 and 6, 6 → 4 space 5.
    assert len(crossings) == 4 + 1 + 4 + 1 + 4 + 1


@pytest.mark.parametrize("name", sorted(_catalogue()))
def test_strands_keep_their_space_and_order(name):
    sinnet = _catalogue()[name]
    disk = sinnet_disk(sinnet, 2)
    where = dict(disk.start)
    for number, step in enumerate(disk.steps):
        for k, delta in step.items():
            where[k] = (where[k] - 1 + delta) % disk.n_slots + 1
        assert len(set(where.values())) == len(where)
        settled = number + 1 == len(disk.steps) or not disk.labels[
            number + 1
        ].startswith("settle")
        if settled:
            # Once a move's spaces have settled, each keeps a free slot at
            # either end, for the next strand to come in.
            for slot in where.values():
                place = (slot - 1) % disk.slots_per_space + 1
                assert 2 <= place < disk.slots_per_space


@pytest.mark.parametrize("name", sorted(_catalogue()))
def test_the_braid_permutes_the_strands_as_the_disk_does(name):
    sinnet = _catalogue()[name]
    disk = sinnet_disk(sinnet)
    end = _end(disk)
    # Read clockwise from the seam, as the word is: slots from the last back.
    first = sorted(disk.start, key=lambda k: -disk.start[k])
    last = sorted(end, key=lambda k: -end[k])
    moved = [last.index(k) for k in first]
    assert _cycles(moved) == _cycles([p - 1 for p in sinnet.braid().perm()])


@pytest.mark.parametrize("name", sorted(_catalogue()))
def test_the_braid_is_the_old_word_read_from_the_other_side(name):
    """Two ways of reading a sinnet, written apart, make the same braid.

    :func:`ashley_to_artin_exact` reads anticlockwise and counts a strand
    lifted over as positive: read clockwise and mirrored, it is the braid.
    """
    sinnet = _catalogue()[name]
    n = sinnet.n_strands
    _, old = ashley_to_artin_exact(list(sinnet.initial_counts_per_space), sinnet.moves)
    other_side = [-int(np.sign(g)) * (n - abs(g)) for g in old]
    assert Braid(other_side + [1], n) == Braid(sinnet.braid().generators + [1], n)


def test_two_moves_from_one_space_are_both_made():
    # A mapping from source to destination cannot hold both.
    _, word = ashley_to_artin_exact([2, 1, 1, 1], [(1, 3), (1, 4)])
    _, first = ashley_to_artin_exact([2, 1, 1, 1], [(1, 3)])
    assert len(word) > len(first)


@pytest.mark.parametrize("name", ["abok_3042", "abok_3047", "abok_3053"])
def test_the_mobidai_pattern_makes_the_same_braid(name):
    sinnet = _catalogue()[name]
    config = sinnet.to_mobidai()
    assert config.n_slots == sinnet_disk(sinnet).n_slots
    assert not config.is_clockwise
    for n_cycles in (1, 2):
        start, steps = mobidai_steps(config, n_cycles)
        word, _ = disk_annular_word(start, steps, config.n_slots, clockwise=False)
        # Strands numbered alike: one per slot, in the order they start.
        assert word == sinnet.annular_word(n_cycles)


def test_a_sinnet_is_animated_strand_by_strand():
    from braidpy.solid_sinnets_catalog import abok_3042

    fig = abok_3042.animate(samples_per_step=2, side_view=True)
    labels = [s.label for s in fig.layout.sliders[0].steps if s.label]
    assert labels[0] == "0 1 → 5"
    assert any("settle" in label for label in labels)
    assert {t.type for t in fig.frames[0].data} == {"scatter", "scatter3d"}
    # The spaces are named, round the rim.
    names = [t for t in fig.data if t.mode == "text"]
    assert [str(x) for x in names[0].text] == ["1", "2", "3", "4", "5", "6"]


def test_a_sinnet_in_3d():
    from braidpy.solid_sinnets_catalog import abok_3042

    braid = abok_3042.braid_3d(0.12, n_cycles=1, iterations=60)
    assert len(braid.points) == 8
    assert braid.closest_approach() > 0.12 * 0.9
