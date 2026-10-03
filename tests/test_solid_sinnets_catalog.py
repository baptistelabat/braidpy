# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The Ashley solid sinnets catalogue can be loaded, and every entry worked."""

import pytest

from braidpy.ashley_solid_sinnet import AshleySolidSinnet, ashley_single_move_to_artin


def _catalogue():
    # It could not be imported at all: it imported ashley_solid_sinnet as a
    # top-level module rather than from braidpy, and a missing comma made one
    # entry call a tuple.
    import braidpy.solid_sinnets_catalog as catalogue

    return {
        name: value
        for name, value in vars(catalogue).items()
        if isinstance(value, AshleySolidSinnet)
    }


def test_the_catalogue_loads_all_its_sinnets():
    assert len(_catalogue()) == 13


@pytest.mark.parametrize("name", sorted(_catalogue()))
def test_every_move_is_between_spaces_and_crosses_real_strands(name):
    sinnet = _catalogue()[name]
    n_spaces = len(sinnet.initial_counts_per_space)
    n_strands = sum(sinnet.initial_counts_per_space)
    counts = list(sinnet.initial_counts_per_space)
    word = []
    for source, target in sinnet.moves:
        assert 1 <= source <= n_spaces and 1 <= target <= n_spaces
        counts, crossings = ashley_single_move_to_artin(counts, source, target)
        word += crossings
    assert word, "a sinnet with no crossings is not a sinnet"
    assert all(1 <= abs(g) <= n_strands - 1 for g in word)
    assert sum(counts) == n_strands
