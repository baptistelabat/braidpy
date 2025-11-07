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
