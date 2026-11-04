# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/settle.js, the page's settle worker, as the page runs it."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "settle_cases.js"


def _run(case, *args):
    out = subprocess.run(
        ["node", str(CASES), case, *map(str, args)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.parametrize(
    "how, twist", [("settled", "keep"), ("settled", "free"), ("formed", "keep")]
)
@pytest.mark.slow
def test_a_twisted_word_settled_by_physics_keeps_or_loses_its_twist(
    tmp_path, how, twist
):
    """σ₁ sixteen times, eight full turns of two yarns, laid round a ring
    and settled by physics as the page settles it.  Held, the yarns keep
    every turn: none is undone by pulling them clear sideways first, nor
    by one passing through the other.  Free, the end turns all eight out."""
    from braidpy.web import build

    spec = {
        "source": "word",
        "word": "1",
        "n_strands": 2,
        "repeat": 16,
        "settle": "physics",
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(build(spec, tighten=False)))
    import numpy as np

    from braidpy.linking import yarn_linking

    result = _run("paged", path, how, twist)
    laid = yarn_linking([np.reshape(y, (-1, 3)) for y in result["laid"]])["links"]
    settled = yarn_linking(
        [np.reshape(y, (-1, 3)) for y in result["settled"]], result["turn"]
    )["links"]
    assert [abs(round(x)) for x in laid] == [8]
    assert settled == pytest.approx(laid, abs=0.01)
    turns = abs(result["turn"]) / (2 * math.pi)
    if twist == "keep":
        assert turns == 0
    else:
        assert turns == pytest.approx(8, abs=0.1)
        assert any(note.startswith("Untwisted") for note in result["notes"])


@pytest.mark.parametrize(
    "spec",
    [
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 4},
        {"source": "mobidai", "name": "KONGO_8", "cycles": 2},
    ],
)
def test_grow_puts_each_moment_of_the_making_back_as_it_was(tmp_path, spec):
    """A braid made on a marudai, its moments kept for Grow with only their
    beads still free, packed and unpacked as the site keeps them: put back,
    each moment is as it was to within the packing's hundredths of a yarn
    diameter, though the braid turned as it went, frozen beads and all."""
    from braidpy.web import build

    path = tmp_path / "laid.json"
    path.write_text(json.dumps(build(spec, tighten=False)))
    result = _run("grown", path)
    assert result["gap"] <= 0.0051
    assert result["turned"] > 0.05
    assert result["frozen"] > 0
