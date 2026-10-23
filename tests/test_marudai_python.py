# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy.marudai, the Python port of web/marudai.js, against it.

Two checks:

- The same algorithm: given the same numbers from the maths library, the
  port makes the very same braid, bead for bead.  Every result of cos, sin,
  atan2 and asin is rounded to single precision on both sides, so that
  Python's library and JavaScript's agree, and the port is given
  JavaScript's ``Math.hypot`` (``tests/js_maths.py``).
- The same braid: each with its own maths library, which differ in the last
  place (Python's ``math.hypot`` is correctly rounded, JavaScript's is not),
  the braids differ — thousands of relaxation steps make a last-place
  difference visible, as any change does — but no more than such a
  difference makes them: the same yarns crossing half way up, as long and
  as thick within its spread, no two yarns closer than a diameter.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from js_maths import rounded_math

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "marudai_cases.js"

# Small braids: the port is pure Python, tens of times slower.
PLAIT = {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 2}
# The bobbins turned round the held braid: twisted in, shuffled.
ROPE = {"source": "word", "word": "1 2 3", "n_strands": 4, "repeat": 4}
# More yarns than the method was made for: tied round two rings, the braid
# turned on each yarn's whole way out.
MANY = {
    "source": "word",
    "word": "1 4 7 -10 13 16 -19 22 25 28",
    "n_strands": 31,
    "repeat": 1,
}


def _js(case, path):
    out = subprocess.run(
        ["node", str(CASES), case, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def _disk(tmp_path, spec):
    from braidpy.web import build

    disk = build(spec, tighten=False)["disk"]
    path = tmp_path / "disk.json"
    path.write_text(json.dumps(disk))
    return disk, path


@pytest.mark.parametrize("spec", [PLAIT, ROPE, MANY], ids=["plait", "rope", "many"])
@pytest.mark.slow
def test_the_port_is_the_same_algorithm_bead_for_bead(tmp_path, monkeypatch, spec):
    from braidpy import marudai

    monkeypatch.setattr(marudai, "math", rounded_math())

    disk, path = _disk(tmp_path, spec)
    js = _js("rounded", path)
    py = marudai.make(disk)
    assert py["updates"] == js["updates"]
    assert py["tip"] == js["tip"]
    assert py["whole"] == js["whole"]


@pytest.mark.parametrize("spec", [{**PLAIT, "repeat": 4}, ROPE], ids=["plait", "rope"])
@pytest.mark.slow
def test_the_port_makes_the_same_braid(tmp_path, spec):
    from braidpy.marudai import make

    disk, path = _disk(tmp_path, spec)
    js = _js("marudai", path)
    made = tmp_path / "made.json"
    made.write_text(json.dumps(make(disk)))
    py = _js("measure", made)
    assert py["crossings"] == js["crossings"]
    assert py["tip"] == pytest.approx(js["tip"], rel=0.3, abs=0.5)
    assert py["radius"] == pytest.approx(js["radius"], rel=0.3)
    assert py["closest"] > 0.85
