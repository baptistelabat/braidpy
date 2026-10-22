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
    assert len(_catalogue()) == 43


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


def test_every_sinnet_has_the_shape_the_book_gives_it():
    """Each entry's shape is its cross-section as the catalogue's own note
    for it names it, as in ABOK ("8-strand round", "11-strand triangle"),
    and its strands are as many as the note says."""
    import inspect
    import re

    import braidpy.solid_sinnets_catalog as catalogue

    notes = re.findall(
        r"ABOK #(\d+)\s*\n\s*(\d+)-strand ([a-z -]+?)\s*\n",
        inspect.getsource(catalogue),
    )
    assert len(notes) == len(_catalogue())
    for number, strands, shape in notes:
        sinnet = _catalogue()[f"abok_{number}"]
        assert sinnet.shape == shape
        assert sinnet.n_strands == int(strands)


@pytest.mark.parametrize(
    "sinnet, word",
    [("abok_2965", "flat3"), ("abok_2999", "square4")],
)
def test_the_simplest_sinnets_are_the_braids_they_are_named_for(sinnet, word):
    """Worked on Ashley's stand, the plait and the square sinnet are the
    braids their braid words make: nothing measured tells them apart."""
    from braidpy.braid_catalog import CATALOGUE as WORDS
    from braidpy.similarity import fingerprint, same_fingerprint

    made = _catalogue()[sinnet].braid(1)
    assert same_fingerprint(fingerprint(made), fingerprint(WORDS[word].make()))


# Sinnets whose moves, as transcribed, do not give every space its strands
# back after a cycle, and for which no one correction is clearly the right
# one: to be checked against the book.
UNCHECKED = {"abok_3051"}


def test_every_cycle_gives_every_space_its_strands_back():
    """In a solid sinnet each space gives a strand and receives one in every
    cycle, so the strands of each space are the same after a cycle — what a
    mistranscribed move breaks."""
    unbalanced = set()
    for name, sinnet in _catalogue().items():
        sources = sorted(a for a, _ in sinnet.moves)
        targets = sorted(b for _, b in sinnet.moves)
        spaces = list(range(1, len(sinnet.initial_counts_per_space) + 1))
        if sources != spaces or targets != spaces:
            unbalanced.add(name)
    assert unbalanced == UNCHECKED
