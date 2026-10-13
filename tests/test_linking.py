# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Linking numbers, from a braid's word and from its yarns in space."""

import numpy as np
import pytest

from braidpy.braid import Braid
from braidpy.linking import (
    close_yarns,
    gauss_linking_number,
    linking_matrix,
    yarn_linking,
)


def _laid(word, n_strands, per_crossing=20):
    """The word laid as braidpy draws it, its row moved off the axis so that
    each end has an angle of its own, rising 3 a crossing; and which bottom
    end each top end joins."""
    from braidpy.parametric_strand import SMOOTHSTEP, strand_paths

    braid = Braid(tuple(word), n_strands)
    paths = strand_paths(braid, spacing=1.5, amplitude=0.7, profile=SMOOTHSTEP)
    zs = np.linspace(0, len(word), per_crossing * len(word) + 1)
    yarns = []
    for path in paths:
        points = np.array([path.position(z) for z in zs])
        points[:, 1] -= 10.0
        points[:, 2] *= 3.0
        yarns.append(points)
    return braid, yarns, braid.slot_history()[-1]


def test_two_strands_twisted_twice_close_into_a_hopf_link():
    assert linking_matrix(Braid((1, 1), 2)).tolist() == [[0, 1], [1, 0]]
    assert linking_matrix(Braid((-1, -1), 2)).tolist() == [[0, -1], [-1, 0]]
    assert linking_matrix(Braid((1, 1, 1, 1), 2))[0, 1] == 2


def test_a_plait_closes_into_one_loop_and_three_plaits_into_three():
    """A plait's strands go round all three slots: its closure is one loop.
    Three plaits bring every strand home, three loops, none linked."""
    assert linking_matrix(Braid((1, -2), 3)).shape == (1, 1)
    assert linking_matrix(Braid((1, -2) * 3, 3)).tolist() == [[0] * 3] * 3


@pytest.mark.parametrize(
    "word, n_strands",
    [
        ((1, 1), 2),
        ((1, 1, 1, 1), 2),
        ((1, -2) * 3, 3),
        ((1, 2, 2, 1), 3),
        ((1, 1, 2, 2, -1, -1), 3),
        ((1, 3, 1, 3), 4),
        ((2, 1, 1, 2, 3, 3), 4),
    ],
)
def test_the_yarns_link_as_the_word_says(word, n_strands):
    """Measured on the yarns, closed up round the outside: the same linking
    numbers as counted from the word — of the opposite sign, braidpy's
    drawing being the mirror image of the usual convention."""
    braid, yarns, pairing = _laid(word, n_strands)
    matrix = linking_matrix(braid)
    measured = yarn_linking(yarns, pairing=pairing)
    assert measured["components"] == len(matrix)
    expected = [
        -matrix[i, j] for i in range(len(matrix)) for j in range(i + 1, len(matrix))
    ]
    assert measured["links"] == pytest.approx(expected, abs=1e-6)


def test_two_rings_one_through_the_other_link_once():
    """The Gauss integral itself: two round rings, one threaded through the
    other, link ±1; moved apart, 0."""
    t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    ring = np.column_stack([np.cos(t), np.sin(t), 0 * t])
    through = np.column_stack([1 + np.cos(t), 0 * t, np.sin(t)])
    assert abs(gauss_linking_number(ring, through)) == pytest.approx(1, abs=1e-9)
    apart = through + np.array([5.0, 0, 0])
    assert gauss_linking_number(ring, apart) == pytest.approx(0, abs=1e-9)


def test_yarns_whose_ends_cannot_pair_up_are_refused():
    yarn = np.array([[1.0, 0, 0], [1.0, 0, 5]])
    with pytest.raises(ValueError, match="pair up"):
        close_yarns([yarn, yarn + [0.001, 0, 0]], pairing=[0, 0])
