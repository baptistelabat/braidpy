# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/b3d.js: a braid made on the marudai, saved as braid3dmin saves one."""

import json
import math
import shutil
import subprocess
import urllib.parse
from pathlib import Path

import pytest

from braidpy.craft_design_online import BraidModel
from braidpy.web import build

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "marudai_cases.js"


def _saved(tmp_path, spec):
    laid = build(spec, tighten=False)
    path = tmp_path / "laid.json"
    path.write_text(json.dumps(laid))
    out = subprocess.run(
        ["node", str(CASES), "b3d", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    made = json.loads(out.stdout)
    return laid, made, json.loads(urllib.parse.unquote(made["text"]))


def test_a_sinnet_is_saved_with_its_yarns_and_every_move(tmp_path):
    """Each yarn, its colour and every bead made; a step to lay them out,
    then one a move, each yarn's angle as braid3dmin's, and after each step
    where every yarn is."""
    laid, made, saved = _saved(
        tmp_path, {"source": "sinnet", "name": "abok_3073", "cycles": 1}
    )
    n = len(laid["strands"])
    assert saved["nThreads"] == n
    colours = [int(s["colour"][1:], 16) for s in laid["strands"]]
    assert [t["colour"] for t in saved["threadStates"]] == colours
    assert [len(t["poss"]) for t in saved["threadStates"]] == made["beads"]
    moving = [step for step in laid["disk"]["steps"] if any(d for _, d in step)]
    steps = saved["steps"]
    assert steps[0]["type"] is None
    assert [step["type"] for step in steps[1:]] == ["threadMove"] * len(moving)
    for step, moves in zip(steps[1:], moving, strict=True):
        assert sorted(m["id"] for m in step["moves"]) == sorted(
            t for t, d in moves if d
        )
        for move in step["moves"]:
            assert -math.pi <= move["from"] <= math.pi
            assert -math.pi <= move["to"] <= math.pi
        assert sorted(int(p["id"]) for p in step["poss"]) == list(range(n))


def test_a_kumihimo_braid_turns_with_its_disk_in_no_step_of_its_own(tmp_path):
    """Turned with every bobbin on it, the disk and the braid turn together,
    nothing moving against anything else: braid3dmin has no such step, and
    the file has none; the moves stay as many as the disk's own."""
    laid, _, saved = _saved(
        tmp_path, {"source": "kumihimo", "n_strands": 8, "repeat": 2}
    )
    n = len(laid["strands"])
    steps = laid["disk"]["steps"]
    turns = [s for s in steps if len(s) == n and len({d for _, d in s}) == 1]
    assert turns
    assert len(saved["steps"]) == 1 + len(steps) - len(turns)


def test_the_file_reads_back_as_braid3dmin_files_do(tmp_path):
    """braidpy's own reader of braid3dmin's files reads it."""
    _, _, saved = _saved(tmp_path, {"source": "sinnet", "name": "abok_3042"})
    path = tmp_path / "braid.b3d"
    path.write_text(urllib.parse.quote(json.dumps(saved)))
    model = BraidModel.load_from_file(str(path))
    assert model.n_strands == saved["nThreads"]
    assert len(model.steps) == len(saved["steps"])
