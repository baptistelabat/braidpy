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
    # Pulled clear first: no yarn starts inside another's core, nor gets
    # far into one on the way.
    assert result["startOverlap"] < 0.01
    assert result["deepestEver"] < 0.05
    assert result["settledHeight"] < 0.5 * result["height"]
    assert result["after"]["components"] == result["before"]["components"]
    before = [round(x) for x in result["before"]["links"]]
    after = [round(x) for x in result["after"]["links"]]
    assert after == before
    # Exact linking numbers are whole: the closures really are closed.
    assert all(abs(x - round(x)) < 0.01 for x in result["after"]["links"])


def test_a_sinnet_made_crossing_by_crossing_is_the_same_braid(tmp_path):
    """ABOK #3044, made row by row with friction as the page makes it, then
    settled: far shorter at each stage, and its closure's loops link each
    other as the laid braid's did."""
    from braidpy.web import build

    spec = {"source": "sinnet", "name": "abok_3044", "cycles": 2, "settle": "crossing"}
    job = tmp_path / "job.json"
    job.write_text(json.dumps(build(spec, tighten=False)["tighten"]))
    result = _run("formed", job)
    assert result["largestForce"] < 1e-3
    assert result["deepestEver"] < 0.05
    assert result["madeHeight"] < 0.5 * result["height"]
    laid = [round(x) for x in result["laid"]["links"]]
    assert [round(x) for x in result["made"]["links"]] == laid
    assert [round(x) for x in result["settled"]["links"]] == laid


def test_a_sinnet_made_on_a_marudai_matches_braid3dmin(tmp_path):
    """ABOK #3044 over 4 cycles, made move by move by marudai.js from
    braidpy's own disk program.  braid3dmin, made to do the same moves,
    makes it 7.27 diameters long, its yarns half way up about 1.5 diameters
    from its axis: so does marudai.js, within what the order beads are
    moved in changes; and no two yarns come much closer than a diameter."""
    from braidpy.web import build

    disk = build({"source": "sinnet", "name": "abok_3044", "cycles": 4}, tighten=False)[
        "disk"
    ]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps(disk))
    result = _run("marudai", program)
    assert result["tip"] == pytest.approx(7.27, rel=0.15)
    assert result["crossings"] == 8
    assert result["radius"] == pytest.approx(1.5, abs=0.25)
    assert result["closest"] > 0.85


def test_a_plait_is_made_on_a_marudai_from_its_word(tmp_path):
    """The plait, its word rolled onto a ring of three bobbins and made move
    by move, each crossing a swap of neighbours: a braid forms, a few
    diameters long, its yarns clear of each other."""
    from braidpy.web import build

    disk = build(
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6}, tighten=False
    )["disk"]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps(disk))
    result = _run("marudai", program)
    assert result["tip"] > 5
    assert result["crossings"] == 3
    assert result["closest"] > 0.85


@pytest.mark.parametrize(
    "word, n_strands, repeat",
    [("1 2 -3 4", 5, 4), ("1 1 1", 2, 2), ("1 2 3", 4, 4)],
)
def test_a_word_made_on_a_marudai_keeps_its_hand(tmp_path, word, n_strands, repeat):
    """Made on a marudai and shown as the page shows it, a braid word is the
    braid braidpy draws for it, not its mirror image: the sum of the Gauss
    linking integrand over pairs of yarns, which a mirror flips, has the
    same sign.  ``1 2 3`` is made by turning the bobbins round the held
    braid, a rope's twist."""
    from braidpy.web import build

    result = build(
        {"source": "word", "word": word, "n_strands": n_strands, "repeat": repeat}
    )
    case = tmp_path / "case.json"
    case.write_text(
        json.dumps(
            {
                "disk": result["disk"],
                "strands": [s["points"][::2] for s in result["strands"]],
            }
        )
    )
    hand = _run("handedness", case)
    assert hand["tip"] > 1
    assert abs(hand["braidpy"]) > 1
    assert hand["made"] * hand["braidpy"] > 0
