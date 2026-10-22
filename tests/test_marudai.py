# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/marudai.js, a braid made move by move as on a marudai."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "marudai_cases.js"


def _run(case, *args):
    out = subprocess.run(
        ["node", str(CASES), case, *map(str, args)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.slow
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


@pytest.mark.parametrize("name", ["abok_3042", "abok_3044"])
@pytest.mark.parametrize("key, layout", [("word", "row"), ("annular_word", "ring")])
@pytest.mark.slow
def test_a_braids_own_word_typed_in_makes_the_same_braid(tmp_path, name, key, layout):
    """The word braidpy gives a sinnet — its braid word, or its ring word —
    typed in as a braid word and made on a marudai is the sinnet again: as
    thick, near enough as long, its yarns clear of each other."""
    from braidpy.web import build

    def made(spec):
        disk = build(spec, tighten=False)["disk"]
        program = tmp_path / "disk.json"
        program.write_text(json.dumps(disk))
        return _run("marudai", program)

    sinnet = build({"source": "sinnet", "name": name, "cycles": 4}, tighten=False)
    info = sinnet["info"]
    own = made({"source": "sinnet", "name": name, "cycles": 4})
    typed = made(
        {
            "source": "word",
            "layout": layout,
            "word": info[key],
            "n_strands": info["n_strands"],
        }
    )
    assert typed["radius"] == pytest.approx(own["radius"], rel=0.15)
    assert typed["tip"] == pytest.approx(own["tip"], rel=0.3)
    assert typed["closest"] > 0.75


@pytest.mark.slow
def test_a_braid_made_on_from_where_it_was_left_is_the_same_braid(tmp_path):
    """Braid Studio makes more of a braid from where it left it: made in two
    goes, it is the braid made at once."""
    from braidpy.web import build

    disk = build({"source": "sinnet", "name": "abok_3042", "cycles": 2}, tighten=False)[
        "disk"
    ]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps(disk))
    result = _run("continued", program)
    assert result["tip"] > 1
    assert result["same"]


@pytest.mark.slow
def test_a_braid_held_is_as_tight_as_one_hanging_free(tmp_path):
    """Held, so that it never turns to balance, a sinnet is drawn as tight as
    hanging free: no slack.  (Braid Studio's "kept".)"""
    from braidpy.web import build

    disk = build({"source": "sinnet", "name": "abok_3042", "cycles": 4}, tighten=False)[
        "disk"
    ]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps(disk))
    free = _run("marudai", program)
    program.write_text(json.dumps({**disk, "held": True, "twists": True}))
    held = _run("marudai", program)
    assert held["radius"] < 1.1 * free["radius"]
    assert held["closest"] > 0.85


def test_a_rope_hanging_free_untwists(tmp_path):
    """The same bobbins turned round a braid left free to turn: it turns
    along with them, and nothing is twisted in — no rope.  (Braid Studio's
    "untwisted".)"""
    from braidpy.web import build

    disk = build(
        {"source": "word", "layout": "ring", "word": "4", "n_strands": 3, "repeat": 12},
        tighten=False,
    )["disk"]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps({**disk, "held": False, "twists": False}))
    assert _run("marudai", program)["tip"] < 1


@pytest.mark.slow
def test_a_rope_is_made_on_a_marudai_with_no_core(tmp_path):
    """Three bobbins turned round the held braid, a place at a time: a
    three-strand rope, each yarn as far from its axis as the others — not
    two twisted round the third, left straight as a core."""
    from braidpy.web import build

    disk = build(
        {"source": "word", "layout": "ring", "word": "4", "n_strands": 3, "repeat": 36},
        tighten=False,
    )["disk"]
    program = tmp_path / "disk.json"
    program.write_text(json.dumps(disk))
    result = _run("marudai", program)
    assert result["tip"] > 10
    assert min(result["radii"]) > 0.6 * max(result["radii"])
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
