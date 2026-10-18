# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy.rope and braidpy.form, the Python ports of web/rope.js and
web/form.js, against them.

Two checks:

- The same algorithm: given the same numbers from the maths library, the
  ports settle and make the very same yarns, bead for bead.  Every result of
  cos and sin is rounded to single precision on both sides, so that
  Python's library and JavaScript's agree, and the ports are given
  JavaScript's ``Math.hypot`` (``tests/js_maths.py``).
- The same braid: each with its own maths library, which differ in the last
  place, the yarns end a few thousandths of a diameter apart — physics at
  rest forgets small differences, unlike a marudai's chaotic shuffles — and
  the braid word read back off them is the word laid.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from js_maths import rounded_math
from test_rope import _read_word, _word_yarns

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "rope_cases.js"
WEB = Path(__file__).parent.parent / "web"

# A plait of six crossings, laid as braidpy lays a word.
PLAIT = [1, -2] * 3
# Pulled taut, its top end free to turn and the yarns' lengths kept: a
# short run, as the test's 2000 steps leave it, not yet at rest.
HELD = {"spacing": 0.5, "force": 1, "turns": True, "steps": 2000, "tolerance": 1e-3}
# Beaten up as the page beats a braid up: fed from bobbins, the beads laid
# out again as the yarn slides in, until at rest.
FED = {
    "spacing": 0.5,
    "force": 0.75,
    "turns": True,
    "feed": 1,
    "stretch": 100,
    "contact": 100,
    "steps": 60000,
    "tolerance": 1e-3,
}
# Made crossing by crossing, with friction, as the page makes it.
MADE = {"row": 1.5, "friction": 0.3, "feed": 1, "weight": 0.75}

# The JavaScript's options by the Python's names.
_PYTHON = {"stepsPerRow": "steps_per_row", "dtMax": "dt_max"}


def _js(case, tmp_path, job):
    path = tmp_path / "job.json"
    path.write_text(json.dumps(job))
    out = subprocess.run(
        ["node", str(CASES), case, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def _node(script, tmp_path, job):
    """rope.js or form.js with its own maths, on a job: ``script`` the body
    of a function of ``job`` returning what to print."""
    path = tmp_path / "job.json"
    path.write_text(json.dumps(job))
    src = (
        f"const rope = require({json.dumps(str(WEB / 'rope.js'))});"
        f"const {{ form }} = require({json.dumps(str(WEB / 'form.js'))});"
        "const job = JSON.parse(require('fs').readFileSync(process.argv[1]));"
        f"console.log(JSON.stringify((() => {{ {script} }})()));"
    )
    out = subprocess.run(
        ["node", "-e", src, str(path)], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout)


def _settled_in_python(yarns, options):
    from braidpy.rope import relay, settle

    return settle([relay(y, 0.5) for y in yarns], **options)


def _made_in_python(yarns, options):
    from braidpy.form import form

    return form(yarns, **{_PYTHON.get(k, k): v for k, v in options.items()})


@pytest.mark.parametrize("options", [HELD, FED], ids=["held", "fed"])
def test_rope_is_the_same_algorithm_bead_for_bead(tmp_path, monkeypatch, options):
    from braidpy import rope

    monkeypatch.setattr(rope, "math", rounded_math())
    yarns = _word_yarns(PLAIT, 3)
    js = _js("roundedSettle", tmp_path, {"yarns": yarns, **options})
    py = _settled_in_python(yarns, options)
    assert py["steps"] == js["steps"]
    assert py["rise"] == js["rise"]
    assert py["turn"] == js["turn"]
    assert py["spacing"] == js["spacing"]
    assert py["yarns"] == js["yarns"]


def test_form_is_the_same_algorithm_bead_for_bead(tmp_path, monkeypatch):
    from braidpy import form, rope

    monkeypatch.setattr(rope, "math", rounded_math())
    monkeypatch.setattr(form, "math", rounded_math())
    yarns = _word_yarns(PLAIT, 3)
    js = _js("roundedForm", tmp_path, {"yarns": yarns, **MADE})
    py = _made_in_python(yarns, MADE)
    assert (py["steps"], py["stages"]) == (js["steps"], js["stages"])
    assert py["offset"] == js["offset"]
    assert py["yarns"] == js["yarns"]


def test_rope_settles_the_same_braid(tmp_path):
    """Each with its own maths, beaten up: beads a few thousandths of a
    diameter apart, and the same plait."""
    yarns = _word_yarns(PLAIT, 3)
    js = _node(
        "const { yarns, ...rest } = job;"
        "return rope.settle({ ...rest, yarns: yarns.map("
        "(y) => Array.from(rope.relay(Float64Array.from(y), 0.5))) });",
        tmp_path,
        {"yarns": yarns, **FED},
    )
    py = _settled_in_python(yarns, FED)
    assert py["largestForce"] < 1e-3
    assert py["rise"] == pytest.approx(js["rise"], abs=0.01)
    assert [len(y) for y in py["yarns"]] == [len(y) for y in js["yarns"]]
    apart = max(
        abs(a - b) for p, q in zip(py["yarns"], js["yarns"]) for a, b in zip(p, q)
    )
    assert apart < 0.01
    assert _read_word(py["yarns"]) == _read_word(js["yarns"]) == PLAIT


def test_form_makes_the_same_braid(tmp_path):
    """Each with its own maths, made crossing by crossing: beaten up as far,
    within a hundredth of the braid's length, and the same plait."""
    yarns = _word_yarns(PLAIT, 3)
    js = _node("return form(job);", tmp_path, {"yarns": yarns, **MADE})
    py = _made_in_python(yarns, MADE)
    assert py["stages"] == js["stages"]
    assert py["offset"] == pytest.approx(js["offset"], rel=0.01)
    assert py["deepestEver"] < 0.05
    assert _read_word(py["yarns"]) == _read_word(js["yarns"]) == PLAIT
