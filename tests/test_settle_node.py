# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids made with Braid Studio's site, settled with it by Node
(web/settle_node.js, run by web/build.py), and kept between builds."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from braidpy.web import build

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

BUILD = Path(__file__).parent.parent / "web" / "build.py"


def _site_build():
    spec = importlib.util.spec_from_file_location("studio_build", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _made(site, specs):
    """A site's braids made with it, laid as braidpy.web.premade lays them."""
    made = site / "made"
    made.mkdir(parents=True)
    index = []
    for number, spec in enumerate(specs):
        (made / f"{number}.json").write_text(json.dumps(build(spec, tighten=False)))
        index.append({"spec": spec, "file": f"{number}.json"})
    (made / "index.json").write_text(json.dumps(index))
    return made


def test_braids_made_with_the_site_are_settled_once_and_kept(tmp_path):
    """Each braid is settled as the page settles it as it comes: one made
    move by move, a braid word or a kumihimo disk's, on a marudai; any
    other, a lace machine's, sideways.  Built again, both
    are taken from where they were kept, not settled again; and what is no
    longer made is cleared from there."""
    studio = _site_build()
    site, cache = tmp_path / "site", tmp_path / "settled"
    word = {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 2}
    disk = {"source": "mobidai", "name": "KONGO_8", "cycles": 2}
    lace = {"source": "lace", "cycles": 2}
    made = _made(site, [word, disk, lace])

    studio._settled(site, cache)
    index = json.loads((made / "index.json").read_text())
    assert [e["settled"] for e in index] == [f"{k}.settled.json" for k in range(3)]
    for entry in index:
        laid = json.loads((made / entry["file"]).read_text())
        tight = json.loads((made / entry["settled"]).read_text())
        assert tight["settled"] == ("marudai" if laid.get("disk") else "sideways")
        assert len(tight["strands"]) == len(laid["strands"])
    assert [
        e["spec"]["source"]
        for e in index
        if "disk" not in json.loads((made / e["file"]).read_text())
    ] == ["lace"]
    kept = {path: path.stat().st_mtime_ns for path in cache.glob("*.json")}
    assert len(kept) == 3

    shutil.rmtree(site)
    made = _made(site, [word])
    studio._settled(site, cache)
    assert (
        json.loads((made / "index.json").read_text())[0]["settled"] == "0.settled.json"
    )
    left = {path: path.stat().st_mtime_ns for path in cache.glob("*.json")}
    assert len(left) == 1 and left.items() <= kept.items()
