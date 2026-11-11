# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Where the catalogued braids come from and are shown: their links."""

from urllib.parse import urlparse

import pytest

from braidpy import (
    braid_catalog,
    machine_catalog,
    mobidai_catalog,
    solid_sinnets_catalog,
)
from braidpy.catalogue import KINDS, Link, ashley

CATALOGUES = [braid_catalog, mobidai_catalog, solid_sinnets_catalog, machine_catalog]


def test_a_link_is_of_a_known_kind():
    assert Link("A video", "video", "https://example.org/v").kind == "video"
    with pytest.raises(ValueError, match="kind"):
        Link("A film", "film")


def test_ashley_names_the_book_and_the_number():
    assert ashley(3042) == Link("The Ashley Book of Knots, #3042", "book")


@pytest.mark.parametrize("catalogue", CATALOGUES, ids=lambda m: m.__name__)
def test_every_link_is_whole(catalogue):
    """A title, a known kind, and a web address if it has one: a book on
    paper, or a post known only by where it was, has none."""
    for name, entry in catalogue.CATALOGUE.items():
        assert isinstance(entry.links, tuple), name
        for link in entry.links:
            assert link.title and link.kind in KINDS, (name, link)
            if link.url:
                address = urlparse(link.url)
                assert address.scheme in ("http", "https") and address.netloc, (
                    name,
                    link,
                )
            assert len(set(entry.links)) == len(entry.links), name


def test_the_reference_is_the_first_link():
    entry = solid_sinnets_catalog.CATALOGUE["abok_3051"]
    assert entry.reference == "The Ashley Book of Knots, #3051"
    assert [link.kind for link in entry.links] == ["book", "video", "video", "post"]


@pytest.mark.slow
def test_the_links_go_with_the_topologies_they_make():
    """Exported with the topology catalogue, and read back alike."""
    from braidpy.topology_catalog import export, load

    data = export()
    linked = [m for t in data for m in t["methods"] if m["links"]]
    assert linked, "some braid has a link"
    sinnet = next(m for t in data for m in t["methods"] if m["name"] == "abok_3051")
    assert sinnet["links"][0] == {
        "title": "The Ashley Book of Knots, #3051",
        "kind": "book",
        "url": "",
    }
    back = load(data)
    assert [m.links for t in back for m in t.methods] == [
        tuple(Link(**link) for link in m["links"]) for t in data for m in t["methods"]
    ]
