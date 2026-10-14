# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/rope.js and web/form.js, the yarns' own physics, against what physics says."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "rope_cases.js"


def _word_yarns(word, n_strands):
    """A braid word laid as braidpy draws it, in yarn diameters: strands
    1.5 apart, a crossing strand riding 0.7 off the row, 3 of rise a
    crossing."""
    from braidpy.braid import Braid
    from braidpy.parametric_strand import SMOOTHSTEP, sample_strands, strand_paths

    paths = strand_paths(
        Braid(tuple(word), n_strands), spacing=1.5, amplitude=0.7, profile=SMOOTHSTEP
    )
    return [y.ravel().tolist() for y in sample_strands(paths, per_unit=20, rise=3.0)]


def _read_word(yarns):
    """The braid word read back off yarns, as braidpy reads a drawn one."""
    from braidpy.parametric_strand import SampledStrand
    from braidpy.symmetric_braid import braid_word

    return braid_word([SampledStrand(y) for y in yarns], n_samples=2000)


def _links(yarns, turn=0.0):
    """The closure's linking numbers, measured on the yarns."""
    from braidpy.linking import yarn_linking

    import numpy as np

    return yarn_linking([np.reshape(y, (-1, 3)) for y in yarns], turn)


def _row_links(yarns, turn=0.0):
    """The closure's linking numbers for a braid laid in a row, a flat braid:
    each yarn's top end, turned back by ``turn``, joined to the bottom end
    below it round the back of the braid, each yarn in a plane of its own,
    so no two closing paths meet.  (:func:`braidpy.linking.close_yarns`
    closes round the outside, as for a round braid: across a row, its paths
    would cross the braid.)"""
    import numpy as np

    from braidpy.linking import gauss_linking_number

    def turned(p, a):
        c, s = math.cos(a), math.sin(a)
        return np.array([c * p[0] - s * p[1], s * p[0] + c * p[1], p[2]])

    ys = [np.reshape(y, (-1, 3)) for y in yarns]
    tops = [turned(y[-1], -turn) for y in ys]
    pairing = [
        int(np.argmin([np.hypot(*(t[:2] - u[0][:2])) for u in ys])) for t in tops
    ]
    assert len(set(pairing)) == len(ys), "The yarns' ends do not pair up."
    above = max(y[:, 2].max() for y in ys) + 2
    below = min(y[:, 2].min() for y in ys) - 2
    behind = max(np.abs(y[:, :2]).max() for y in ys) + 3
    closed = []
    for a, y in enumerate(ys):
        up = [turned(y[-1], -turn * k / 30) + [0, 0, 0.05 * k] for k in range(1, 31)]
        top, bottom = up[-1], ys[pairing[a]][0]
        lift, sink, plane = above + a, below - a, behind + a
        back = [
            [top[0], top[1], lift],
            [top[0], plane, lift],
            [top[0], plane, sink],
            [bottom[0], plane, sink],
            [bottom[0], bottom[1], sink],
        ]
        closed.append(np.vstack([y, up, back]))
    seen = [False] * len(ys)
    loops = []
    for first in range(len(ys)):
        parts, a = [], first
        while not seen[a]:
            seen[a] = True
            parts.append(closed[a])
            a = pairing[a]
        if parts:
            loops.append(np.vstack(parts))
    return [
        gauss_linking_number(loops[i], loops[j])
        for i in range(len(loops))
        for j in range(i + 1, len(loops))
    ]


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


def test_a_two_ply_rope_free_to_turn_untwists():
    """The same rope, its end free to turn: with nothing to hold it, it
    untwists, as a frictionless rope must — very nearly both its turns, the
    yarns' clamped ends keeping a little — and rises almost to their length,
    side by side."""
    result = _run("twoPlyFree")
    assert result["largestForce"] < 1e-3
    assert abs(result["turn"]) / (2 * math.pi) == pytest.approx(2, abs=0.1)
    assert 10 + result["rise"] == pytest.approx(result["length"], rel=0.02)


def test_a_plait_pulled_taut_stays_the_same_plait(tmp_path):
    """A three-strand plait, its end free to turn: pulled taut, its yarns
    never pass through one another, so it is the same braid at rest — and
    turning its end could not undo it, so it barely turns."""
    word = [1, -2, 1, -2]
    laid = tmp_path / "laid.json"
    laid.write_text(json.dumps(_word_yarns(word, 3)))
    result = _run("word", laid)
    assert result["largestForce"] < 1e-3
    assert _read_word(result["yarns"]) == word
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
    before = _links(result["laid"])
    after = _links(result["settled"], result["turn"])
    assert after["components"] == before["components"]
    assert [round(x) for x in after["links"]] == [round(x) for x in before["links"]]
    # Exact linking numbers are whole: the closures really are closed.
    assert all(abs(x - round(x)) < 0.01 for x in after["links"])


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
    laid = [round(x) for x in _links(result["laid"])["links"]]
    assert [round(x) for x in _links(result["made"])["links"]] == laid
    settled = _links(result["settled"], result["turn"])["links"]
    assert [round(x) for x in settled] == laid


@pytest.mark.parametrize(
    "name, flat", [("tubular_12", False), ("soutache_5", True)], ids=str
)
def test_a_machine_braid_on_its_fell_ring_settles_as_the_same_braid(
    tmp_path, name, flat
):
    """A machine's braid is laid on a fell ring the size of the braid, not
    drawn in to a point where every yarn would meet: beaten up by physics,
    far shorter, no yarn has passed through another — its closure's loops
    link each other as they did.  Soutache's cores, of yarn, settle as
    yarns."""
    from braidpy.web import build

    spec = {"source": "machine", "name": name, "cycles": 2, "settle": "physics"}
    job = tmp_path / "job.json"
    job.write_text(json.dumps(build(spec, tighten=False)["tighten"]))
    result = _run("sinnet", job)
    assert result["largestForce"] < 1e-3
    assert result["deepestEver"] < 0.05
    assert result["settledHeight"] < 0.5 * result["height"]
    if flat:
        before = _row_links(result["laid"])
        after = _row_links(result["settled"], result["turn"])
    else:
        before = _links(result["laid"])["links"]
        after = _links(result["settled"], result["turn"])["links"]
    # Some loops do link: the check checks something.
    assert any(round(x) for x in before)
    assert [round(x) for x in after] == [round(x) for x in before]
    assert all(abs(x - round(x)) < 0.01 for x in before + after)
