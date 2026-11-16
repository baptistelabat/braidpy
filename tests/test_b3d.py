# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/b3d.js: a braid made on the marudai, saved as braid3dmin saves one."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from braidpy.b3d import Design, read_b3d, write_b3d
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
    return laid, made, read_b3d(made["text"])


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
    the file has none.  A strand taken across the disk, half a turn or more,
    is two steps, each less than half a turn: a move's angles say only the
    short way round."""
    laid, _, saved = _saved(
        tmp_path, {"source": "kumihimo", "n_strands": 8, "repeat": 2}
    )
    n = len(laid["strands"])
    n_slots = laid["disk"]["n_slots"]
    steps = laid["disk"]["steps"]
    turns = [s for s in steps if len(s) == n and len({d for _, d in s}) == 1]
    across = [
        s for s in steps if s not in turns and any(2 * abs(d) >= n_slots for _, d in s)
    ]
    assert turns and across
    assert len(saved["steps"]) == 1 + len(steps) - len(turns) + len(across)
    for step in saved["steps"][1:]:
        for move in step["moves"]:
            turn = (move["to"] - move["from"] + math.pi) % (2 * math.pi) - math.pi
            assert abs(turn) < math.pi


def test_the_file_reads_back_as_braid3dmin_files_do(tmp_path):
    """As braid3dmin writes its own files, each step says where the yarns are
    before it: the first, where they start, as the second does; braidpy's
    reader of them finds every yarn where the file says it starts."""
    laid, _, saved = _saved(tmp_path, {"source": "sinnet", "name": "abok_3042"})
    first, second = saved["steps"][0]["poss"], saved["steps"][1]["poss"]
    assert first == second
    design = Design.read(write_b3d(saved))
    assert sorted(design.start) == list(range(len(laid["strands"])))


def test_a_sinnet_comes_round_and_is_saved_as_one_cycle_and_a_repeat(tmp_path):
    """A sinnet's cycle comes round exactly: the same moves at the same
    angles, the yarns back on the same angles.  Saved over three cycles, it
    is its first cycle — the same steps as a sinnet of one cycle — and a
    repeat that plays it twice more, putting no yarn back first."""
    spec = {"source": "sinnet", "name": "abok_3044"}
    _, _, once = _saved(tmp_path, {**spec, "cycles": 1})
    _, _, thrice = _saved(tmp_path, {**spec, "cycles": 3})
    *cycle, repeat = thrice["steps"]
    assert len(cycle) == len(once["steps"])
    for ours, alone in zip(cycle, once["steps"], strict=True):
        assert [(m["from"], m["to"]) for m in ours["moves"]] == pytest.approx(
            [(m["from"], m["to"]) for m in alone["moves"]]
        )
    assert repeat["type"] == "repeat"
    assert repeat["repeatFrom"] == 1
    assert repeat["repeatTimes"] == 2
    assert repeat["moves"] == []
    assert repeat["rotate"] == 0


@pytest.mark.slow
@pytest.mark.parametrize(
    "spec",
    [
        {"source": "mobidai", "name": "KONGO_8", "cycles": 3},
        {"source": "mobidai", "name": "EDO_YATSU", "cycles": 2},
        {"source": "sinnet", "name": "abok_3044", "cycles": 3},
        {"source": "sinnet", "name": "abok_3073", "cycles": 1},
    ],
)
def test_a_braid_saved_for_braid3d_reads_back_as_the_same_braid(tmp_path, spec):
    """Saved for braid3d and read back (braidpy.b3d), a disk braid or a
    sinnet is the same braid, crossing for crossing: its yarns sliding
    along together in a step, and a sinnet's repeat, read as made."""
    from braidpy.topology_catalog import braid_of
    from braidpy.web import from_b3d

    laid, _, saved = _saved(tmp_path, spec)
    back = build(from_b3d(write_b3d(saved)), tighten=False)
    assert braid_of(back["info"]) == braid_of(laid["info"])


@pytest.mark.slow
def test_a_kumihimo_braid_reads_back_as_made_with_the_disk_turning_along(tmp_path):
    """Saved for braid3d and read back, a kumihimo braid is its moves made
    with the braid turning along with the disk — the file leaves the disk's
    turns out — each strand taken across the disk going the long way round
    it went, in two steps: the braid braidpy's own word gives with its turns
    left out, by every measure of its fingerprint."""
    from braidpy.similarity import fingerprint, same_fingerprint
    from braidpy.take_off import kumihimo_steps
    from braidpy.topology_catalog import braid_of
    from braidpy.web import from_b3d
    from braidpy.web._info import _disk_info

    _, _, saved = _saved(tmp_path, {"source": "kumihimo", "n_strands": 8, "repeat": 2})
    back = braid_of(build(from_b3d(write_b3d(saved)), tighten=False)["info"])
    n_slots, start, steps = kumihimo_steps("SR" * 2, 8)
    n = len(start)
    moves = [s for s in steps if not (len(s) == n and len(set(s.values())) == 1)]
    made = braid_of(
        {**_disk_info(start, moves, n_slots, clockwise=False), "n_strands": n}
    )
    assert same_fingerprint(fingerprint(back), fingerprint(made))
