# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/rope.js, the yarns' own physics, against what physics says."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "rope_cases.js"


def _run(case, *args):
    out = subprocess.run(
        ["node", str(CASES), case, *map(str, args)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def test_a_two_ply_rope_pulled_taut_twists_tight():
    """Two yarns twisted twice round each other, their ends held from
    turning, pulled up: they close in until they touch, a helix of radius
    half a diameter, and rise as far as their length lets them."""
    result = _run("twoPly")
    assert result["largestForce"] < 1e-3
    assert result["radius"] == pytest.approx(0.5, abs=0.02)
    assert result["deepest"] < 0.01
    # Barely stretched.
    assert result["after"] == pytest.approx(result["before"], rel=0.01)
    # As tight all along, the yarn would rise to this; its clamped ends,
    # wider apart, keep it a little lower.
    tight = math.sqrt(result["before"] ** 2 - (2 * math.pi * 0.5 * 2) ** 2)
    assert 0.95 * tight < result["height"] < tight


def test_a_plait_pulled_taut_stays_the_same_plait():
    """A three-strand plait, its end free to turn: pulled taut, its yarns
    never pass through one another, so it is the same braid at rest — and
    turning its end could not undo it, so it barely turns."""
    result = _run("plait")
    assert result["largestForce"] < 1e-3
    assert result["settled"] == result["laid"]
    assert result["deepest"] < 0.01
    assert abs(result["turn"]) < 0.2 * 2 * math.pi


def test_a_sinnet_beaten_up_is_the_same_braid(tmp_path):
    """ABOK #3044, laid by braidpy and beaten up as the page beats it up:
    far shorter, and no yarn has passed through another — its closure's
    loops link each other as they did."""
    from braidpy.web import build

    spec = {"source": "sinnet", "name": "abok_3044", "cycles": 2, "settle": "physics"}
    job = tmp_path / "job.json"
    job.write_text(json.dumps(build(spec, tighten=False)["tighten"]))
    result = _run("sinnet", job)
    assert result["largestForce"] < 1e-3
    assert result["settledHeight"] < 0.5 * result["height"]
    assert result["after"]["components"] == result["before"]["components"]
    before = [round(x) for x in result["before"]["links"]]
    after = [round(x) for x in result["after"]["links"]]
    assert after == before
    # Exact linking numbers are whole: the closures really are closed.
    assert all(abs(x - round(x)) < 0.01 for x in result["after"]["links"])
