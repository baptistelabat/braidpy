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


def _run(case):
    out = subprocess.run(
        ["node", str(CASES), case], capture_output=True, text=True, check=True
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
