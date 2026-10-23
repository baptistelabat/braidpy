# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids compared by their topology, not by how they are written down."""

import time

import pytest

from braidpy import Braid
from braidpy.similarity import distance, fingerprint, similar

PLAIT = [1, -2]


def _rotations(word):
    return [word[i:] + word[:i] for i in range(len(word))]


@pytest.mark.parametrize(
    "word, n_strands",
    [(PLAIT * 3, 3), ([1, -2, 3, -2] * 2, 4), ([1, 2, -1, 3, -2, 1] * 2, 4)],
)
def test_a_fingerprint_does_not_see_how_the_braid_is_written(word, n_strands):
    """From another starting point, repeated more, or its strands numbered
    from the other side, it is the same braid, with the same fingerprint."""
    want = fingerprint(Braid(word, n_strands))
    written = _rotations(word) + [word * 3]
    written.append([(n_strands - abs(g)) * (1 if g > 0 else -1) for g in word])
    for other in written:
        assert distance(fingerprint(Braid(other, n_strands)), want) < 1e-9


def test_the_plait_is_not_strands_hanging_straight():
    """Their linking numbers are all 0 alike: the Alexander polynomial
    tells them apart."""
    plait = fingerprint(Braid(PLAIT * 3, 3))
    straight = fingerprint(Braid([], 3))
    assert plait.linking == straight.linking
    assert plait.alexander != straight.alexander
    assert distance(plait, straight) > 0.5


def test_a_mirror_image_is_told_apart_by_its_writhe():
    """A rope twisted the other way: the same Alexander polynomial, the
    other writhe."""
    s_twist = fingerprint(Braid([1, 1, 1], 2))
    z_twist = fingerprint(Braid([-1, -1, -1], 2))
    assert s_twist.alexander == z_twist.alexander
    assert s_twist.writhe == -z_twist.writhe
    assert distance(s_twist, z_twist) > 0.5


def test_your_own_braid_finds_the_catalogue_braid_it_is():
    """The plait, typed from its second crossing and repeated five times:
    the catalogue's plait comes first, the same fingerprint, at distance 0."""
    mine = Braid((PLAIT[1:] + PLAIT[:1]) * 5, 3)
    found = similar(mine, count=3)
    assert found[0].name in {"flat3", "inverted_flat3"}
    assert found[0].same_fingerprint
    assert found[0].distance < 1e-9


def test_a_braid_unlike_any_still_gets_its_nearest():
    found = similar(Braid([1, 2, 3, -2, 1], 4), count=4)
    assert len(found) == 4
    assert not any(m.same_fingerprint for m in found)
    assert [m.distance for m in found] == sorted(m.distance for m in found)


def test_a_long_sinnet_is_fingerprinted_quickly():
    """ABOK #3048: 17 strands, its 85-crossing unit repeated 60 times
    before every strand is home — the Alexander polynomial sampled, not
    expanded."""
    from braidpy.web import build

    info = build({"source": "sinnet", "name": "abok_3048", "cycles": 1}, tighten=False)[
        "info"
    ]
    braid = Braid([int(g) for g in info["word"].split()], info["n_strands"])
    started = time.perf_counter()
    found = fingerprint(braid)
    assert time.perf_counter() - started < 10
    assert found.n_strands == 17
    assert all(value is not None for value in found.alexander)
