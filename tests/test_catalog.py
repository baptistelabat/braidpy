# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Every catalog lists its braids the same way."""

import importlib

import pytest

from braidpy.catalog import Entry

CATALOGS = {
    "braidpy.braid_catalog": "braidpy.braid.Braid",
    "braidpy.mobidai_catalog": "braidpy.mobidai_catalog.CatalogedMobidai",
    "braidpy.solid_sinnets_catalog": "braidpy.ashley_solid_sinnet.AshleySolidSinnet",
    "braidpy.machine_catalog": "braidpy.horn_gear.model.BraidingMachine",
}


def _class(path):
    module, name = path.rsplit(".", 1)
    return getattr(importlib.import_module(module), name)


@pytest.mark.parametrize("module, kind", sorted(CATALOGS.items()))
def test_a_catalog_names_titles_and_makes_each_braid(module, kind, monkeypatch):
    from braidpy.braid import Braid

    def no_drawing(*args, **kwargs):
        raise AssertionError("drawn")

    monkeypatch.setattr(Braid, "draw", no_drawing)
    catalog = importlib.import_module(module).CATALOG
    assert catalog
    titles = [entry.title for entry in catalog.values()]
    assert len(set(titles)) == len(titles)
    for name, entry in catalog.items():
        assert isinstance(entry, Entry), name
        assert name.isidentifier() and entry.title, name
        assert isinstance(entry.make(), _class(kind)), name


def test_the_mobidai_braid_keeps_its_old_name():
    from braidpy.mobidai_catalog import CataloguedBraid, CataloguedMobidai

    assert CataloguedBraid is CataloguedMobidai
