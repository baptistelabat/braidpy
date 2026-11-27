# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braids made with Braid Studio's site, settled with it by Node
(web/settle_node.js, run by web/build.py), and kept between builds."""

import importlib.util
import json
import math
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
    move by move, a braid word, a kumihimo disk's or a lace machine's, on a
    marudai; any other, a braiding machine's, sideways.  Built again, both
    are taken from where they were kept, not settled again; and what is no
    longer made is cleared from there."""
    studio = _site_build()
    site, cache = tmp_path / "site", tmp_path / "settled"
    word = {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 2}
    disk = {"source": "mobidai", "name": "KONGO_8", "cycles": 2}
    machine = {"source": "machine", "name": "flat_3", "cycles": 1}
    made = _made(site, [word, disk, machine])

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
    ] == ["machine"]
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


def test_a_braid_round_a_core_is_settled_on_the_marudai_with_it(tmp_path):
    """The core settled with the yarns, as the last strand: up the middle,
    and its tail straight up, not across the mirror to a bobbin."""
    studio = _site_build()
    site, cache = tmp_path / "site", tmp_path / "settled"
    spec = {"source": "kumihimo", "repeat": 3, "core": "rigid"}
    made = _made(site, [spec])
    studio._settled(site, cache)
    entry = json.loads((made / "index.json").read_text())[0]
    laid = json.loads((made / entry["file"]).read_text())
    tight = json.loads((made / entry["settled"]).read_text())
    assert tight["settled"] == "marudai"
    assert len(tight["strands"]) == len(laid["strands"])
    assert tight["strands"][-1]["name"] == "Core"
    # Straight up, as rigid.
    core = tight["strands"][-1]["points"]
    assert max(math.dist(p[:2], core[0][:2]) for p in core) < 1e-3
    tails = tight["marudai"]["tails"]
    assert max(math.hypot(x, y) for x, y, _ in tails[-1]) < 1e-3
    # A yarn's tail goes out across the mirror.
    assert math.hypot(*tails[0][-1][:2]) > 1
