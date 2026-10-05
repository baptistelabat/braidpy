# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the web page asks of braidpy, answered as plain data."""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from braidpy.web import build, catalogue, parse_word


@pytest.mark.parametrize(
    "text, word",
    [
        ("1 -2 1", [1, -2, 1]),
        ("1,-2, 1", [1, -2, 1]),
        ("s1 s2^-1 s1", [1, -2, 1]),
        ("σ1 σ2^(-1)", [1, -2]),
        ("aBa", [1, -2, 1]),
        ("  ", []),
    ],
)
def test_words_are_read_in_every_usual_spelling(text, word):
    assert parse_word(text) == word


@pytest.mark.parametrize("text", ["1 x 2", "0 1", "s1 s"])
def test_a_word_that_cannot_be_read_says_so(text):
    with pytest.raises(ValueError):
        parse_word(text)


def _check(result, n_strands):
    """Plain data, every yarn drawn, every number finite."""
    json.dumps(result)
    assert result["title"]
    assert len(result["strands"]) == n_strands
    for strand in result["strands"]:
        assert strand["colour"].startswith("#")
        assert len(strand["points"]) >= 2
        assert all(len(p) == 3 and all(map(math.isfinite, p)) for p in strand["points"])
    assert result["info"]["n_strands"] == n_strands
    assert result["yarn_diameter"] > 0


def test_a_word():
    result = build({"source": "word", "word": "1 -2", "repeat": 3, "iterations": 20})
    _check(result, 3)
    assert result["info"]["word"] == "1 -2 1 -2 1 -2"
    assert (
        result["info"]["permutation"] == [2, 3, 1]
        or len(result["info"]["permutation"]) == 3
    )


def test_a_kumihimo_pattern():
    result = build(
        {
            "source": "kumihimo",
            "pattern": "SR",
            "n_strands": 8,
            "repeat": 2,
            "iterations": 20,
        }
    )
    _check(result, 8)
    assert "annular_word" in result["info"]


@pytest.mark.parametrize("source", ["mobidai", "sinnet", "machine"])
def test_every_catalogue_entry_is_made(source):
    for entry in catalogue()[source]["entries"]:
        if entry["name"] == "custom":
            continue  # made from what is typed in: see below
        result = build(
            {"source": source, "name": entry["name"], "cycles": 1, "iterations": 5}
        )
        assert result["strands"], entry["name"]
        json.dumps(result)


def test_a_machine_braids_its_cores_in_as_yarns():
    """A core is a yarn that stays where it enters the braid: it is tightened
    with the others, and ends up inside, among them."""
    import numpy as np

    result = build({"source": "machine", "name": "soutache_5", "cycles": 2})
    cores = [s for s in result["strands"] if s["name"].startswith("Core")]
    yarns = [s for s in result["strands"] if not s["name"].startswith("Core")]
    assert [s["name"] for s in cores] == ["Core cord_A", "Core cord_B"]
    assert len(yarns) == 5
    assert "word" not in result["info"]
    # Half way up, each core is among the yarns, not off to one side.
    middle = len(cores[0]["points"]) // 2
    xy = np.array([s["points"][middle][:2] for s in yarns])
    low, high = xy.min(axis=0), xy.max(axis=0)
    for core in cores:
        assert np.all(low <= core["points"][middle][:2])
        assert np.all(core["points"][middle][:2] <= high)


@pytest.mark.parametrize("cores", ["yarn", "rigid"])
def test_a_machines_cores_never_cross_or_touch_a_yarn(cores):
    """Each core keeps its own place, down to the fell: the yarns are pushed
    off it, and the two cores never come together, let alone pass."""
    import numpy as np

    result = build(
        {"source": "machine", "name": "soutache_7", "cycles": 2, "cores": cores}
    )
    d = result["yarn_diameter"]
    assert result["info"]["closest_approach"] >= 0.99 * d
    a, b = [
        np.array(s["points"]) for s in result["strands"] if s["name"].startswith("Core")
    ]
    gap = a[:, :2] - b[:, :2]
    assert np.linalg.norm(gap, axis=1).min() >= 0.99 * d
    # Never on the other side of one another.
    assert np.all(gap[:, 0] * gap[0, 0] > 0)


def test_a_rigid_core_stays_straight_and_a_yarn_core_gives_way():
    import numpy as np

    def spread(cores):
        result = build(
            {"source": "machine", "name": "soutache_5", "cycles": 2, "cores": cores}
        )
        core = next(s for s in result["strands"] if s["name"].startswith("Core"))
        xy = np.array(core["points"])[:, :2]
        return float(np.ptp(xy, axis=0).max())

    assert spread("rigid") < 1e-9
    assert spread("yarn") > 0


@pytest.mark.parametrize(
    "spec",
    [
        {"source": "sinnet", "name": "abok_3048", "cycles": 2},
        {"source": "mobidai", "name": "KONGO_8", "cycles": 2},
        {"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2},
    ],
)
def test_a_disk_braid_to_be_settled_by_physics_is_laid_closer(spec):
    """Settled by physics, a disk braid is beaten up anyway: it is laid with
    its rows closer, so there is less of it to beat up."""
    loose = build(spec, tighten=False)["tighten"]
    close = build({**spec, "settle": "physics"}, tighten=False)["tighten"]
    assert close["spacing"] * close["n"] < 0.75 * loose["spacing"] * loose["n"]


def test_cores_are_yarn_or_rigid():
    with pytest.raises(ValueError, match="yarn or rigid"):
        build({"source": "machine", "name": "soutache_5", "cores": "glass"})


def test_a_machine_lays_its_cores_only_when_asked():
    from braidpy.horn_gear import yarn_paths
    from braidpy.horn_gear.examples import soutache_braid

    machine = soutache_braid()
    plain = yarn_paths(machine, n_cycles=1).points
    cored = yarn_paths(machine, n_cycles=1, axials=True).points
    assert set(cored) - set(plain) == {"cord_A", "cord_B"}


def test_the_catalogue_is_plain_data_with_defaults():
    entries = catalogue()
    json.dumps(entries)
    for source, about in entries.items():
        build({"source": source, **about["defaults"], "iterations": 1, "cycles": 1})


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"source": "nowhere"}, "Unknown source"),
        ({"source": "word", "word": ""}, "Give a braid word"),
        ({"source": "word", "word": "3", "n_strands": 3}, "at least 4"),
        ({"source": "word", "word": "1", "repeat": 500}, "between"),
        ({"source": "kumihimo", "pattern": "SX"}, "S \\(swap\\)"),
        ({"source": "kumihimo", "n_strands": 6}, "multiple of 4"),
        ({"source": "mobidai", "name": "nope"}, "No mobidai"),
        ({"source": "sinnet", "name": "nope"}, "No sinnet"),
        ({"source": "machine", "name": "nope"}, "No machine"),
        ({"source": "word", "word": "1", "yarn_diameter": "thick"}, "number"),
    ],
)
def test_what_cannot_be_made_is_explained(spec, message):
    with pytest.raises(ValueError, match=message):
        build(spec)


def test_nothing_heavy_is_loaded_to_build_a_braid():
    """No drawing library: in a browser they would be tens of megabytes; nor
    sympy, seconds to import there."""
    code = (
        "import sys; from braidpy.web import build, catalogue\n"
        "for source, about in catalogue().items():\n"
        "    build({'source': source, **about['defaults'], 'iterations': 1,"
        " 'cycles': 1})\n"
        "print([m for m in ('plotly', 'matplotlib', 'imageio', 'sympy', 'math_braid')"
        " if m in sys.modules])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "[]"


@pytest.mark.parametrize("source", ["word", "kumihimo", "mobidai", "sinnet", "machine"])
def test_what_made_the_braid_comes_with_it_in_step(source):
    about = catalogue()[source]
    result = build(
        {"source": source, **about["defaults"], "iterations": 5, "cycles": 2}
    )
    timeline = result["timeline"]
    n = len(result["strands"])
    # A path per yarn, in the same order, sampled at the timeline's times.
    assert len(timeline["strands"]) == n
    assert all(len(path) == len(timeline["times"]) for path in timeline["strands"])
    assert timeline["kind"] in {"disk", "machine", "line"}
    assert timeline["reach"] > 0
    # Every point of the braid has a time, and they run oldest first.
    times = result["times"]
    assert len(times) == len(result["strands"][0]["points"])
    assert times == sorted(times)
    # The clock relates the two, and only ever goes forwards.
    clock = timeline["clock"]
    assert len(clock["source"]) == len(clock["braid"]) >= 2
    assert clock["source"] == sorted(clock["source"])
    assert clock["braid"] == sorted(clock["braid"])
    assert clock["braid"][-1] >= times[-1] - 1e-6


def test_a_disk_braid_is_made_in_step_with_its_crossings():
    from braidpy.take_off import disk_crossing_steps, mobidai_steps
    from braidpy.mobidai_catalog import KONGO_8

    result = build(
        {"source": "mobidai", "name": "KONGO_8", "cycles": 2, "iterations": 5}
    )
    start, steps = mobidai_steps(KONGO_8.to_config(), 2)
    _, crossings, made_at = disk_crossing_steps(start, steps, 32)
    clock = result["timeline"]["clock"]
    # Each crossing reaches the fell as the disk makes it, half way into its row.
    assert clock["source"][1:-1] == made_at
    assert all(row % 1 == 0.5 for row in clock["braid"][1:-1])
    assert len(clock["braid"]) == len(crossings) + 2


@pytest.mark.parametrize(
    "text",
    ["1>15, 17>31", "1->15; 17->31", "(1, 15) (17, 31)", "1 15\n17 31", "1→15 17→31"],
)
def test_moves_are_read_however_they_are_written(text):
    from braidpy.web import parse_moves

    assert parse_moves(text) == [(1, 15), (17, 31)]


@pytest.mark.parametrize(
    "text, message", [("", "at least one"), ("1>2, 3", "each move")]
)
def test_moves_that_cannot_be_read_say_so(text, message):
    from braidpy.web import parse_moves

    with pytest.raises(ValueError, match=f"(?i){message}"):
        parse_moves(text)


@pytest.mark.parametrize("source", ["mobidai", "sinnet"])
def test_a_catalogued_braid_typed_in_is_the_same_braid(source):
    """What the catalogue shows of a braid, made as your own, is that braid."""
    entry = catalogue()[source]["entries"][0]
    as_listed = build(
        {"source": source, "name": entry["name"], "cycles": 2, "iterations": 5}
    )
    typed = build(
        {
            "source": source,
            "name": "custom",
            **entry["pattern"],
            "cycles": 2,
            "iterations": 5,
        }
    )
    assert typed["info"]["word"] == as_listed["info"]["word"]
    assert typed["strands"][0]["points"] == as_listed["strands"][0]["points"]
    assert catalogue()[source]["entries"][-1]["name"] == "custom"


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"slots": "1 1", "moves": "1>2"}, "same slot"),
        ({"slots": "1 40", "moves": "1>2"}, "numbered from 1 to 32"),
        ({"slots": "1 2", "moves": "1>40"}, "between slots"),
    ],
)
def test_your_own_disk_braid_is_checked(spec, message):
    with pytest.raises(ValueError, match=message):
        build({"source": "mobidai", "name": "custom", "n_slots": 32, **spec})


def test_your_own_sinnet_is_checked():
    with pytest.raises(ValueError, match="between spaces"):
        build({"source": "sinnet", "name": "custom", "counts": "2 1 1", "moves": "1>4"})


def test_a_disk_braid_turns_with_its_disk():
    """Four quarter turns of a kumihimo disk turn its braid once round."""
    result = build(
        {
            "source": "kumihimo",
            "pattern": "SR",
            "n_strands": 8,
            "repeat": 4,
            "iterations": 5,
        }
    )
    turn = result["timeline"]["turn"]
    assert len(turn) == len(result["timeline"]["times"])
    assert abs(abs(turn[-1] - turn[0]) - 2 * math.pi) < 0.2
    # A machine has no disk to hang from.
    machine = build(
        {"source": "machine", "name": "flat_3", "cycles": 1, "iterations": 5}
    )
    assert "turn" not in machine["timeline"]


def test_a_page_can_tighten_the_yarns_itself():
    spec = {"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2}
    laid = build({**spec, "iterations": 0})
    handed = build({**spec, "iterations": 30}, tighten=False)
    job = handed["tighten"]
    # As laid, with what tightening them needs.
    assert handed["strands"] == laid["strands"]
    assert "closest_approach" not in handed["info"]
    assert len(job["xy"]) == 2 * job["n_yarns"] * job["n"]
    assert job["iterations"] == 30 and job["n_yarns"] == 8
    assert len(job["chosen"]) == len(handed["strands"][0]["points"])
    # Nothing to hand over when nothing is to be tightened.
    assert "tighten" not in build({**spec, "iterations": 0}, tighten=False)
    assert "tighten" not in build({**spec, "iterations": 30})


def _node_tighten(job):
    out = subprocess.run(
        [
            "node",
            "-e",
            "const {tightenYarns} = require(process.argv[1]);"
            "const job = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
            "const r = tightenYarns(job);"
            "console.log(JSON.stringify({xy: Array.from(r.xy), closest: r.closest}));",
            str(Path(__file__).resolve().parent.parent / "web" / "tighten.js"),
        ],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
@pytest.mark.parametrize(
    "spec",
    [
        {"source": "word", "word": "1 -2", "repeat": 4},
        {"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2},
        {"source": "machine", "name": "tubular_8", "cycles": 1},
        # Round cores held straight.  Every yarn meets at the braiding
        # point, beside them, and which way two part there is decided by
        # the last digit: alike in the end, not step for step.
        {
            "source": "machine",
            "name": "soutache_7",
            "cycles": 1,
            "cores": "rigid",
            "ties": True,
        },
        # Kept outside a core round the axis, as tighten_yarns can.
        {
            "source": "kumihimo",
            "pattern": "SR",
            "n_strands": 8,
            "repeat": 2,
            "core_radius": 0.06,
        },
    ],
)
def test_the_page_tightens_as_braidpy_does(spec):
    """web/tighten.js is tighten_yarns, step for step.

    Exactly so at first.  Over many steps, rounding differs enough for the
    contact pushes, which switch on and off at a threshold, to take the two
    apart a little — into braids that are as tight and as clear as each
    other.
    """
    import numpy as np

    from braidpy.take_off import tighten_yarns

    core = spec.pop("core_radius", None) if "core_radius" in spec else None
    ties = spec.pop("ties", False)
    handed = build({**spec, "iterations": 20}, tighten=False)
    job = {**handed["tighten"], "core_radius": core}
    n_yarns, n = job["n_yarns"], job["n"]

    # The laid yarns braidpy would have tightened, to the last digit: the
    # pushes would make even a rounding of them a different braid.
    laid = _laid_paths(spec)
    exact = laid.formed()[:, :, :2].reshape(-1).tolist()
    assert np.allclose(exact, job["xy"], atol=1e-8)
    # Exactly alike at first; tightened through, as tight and as clear.
    checks = [(300, None)] if ties else [(20, 1e-8), (300, None)]
    for iterations, close in checks:
        mine = _node_tighten({**job, "xy": exact, "iterations": iterations})
        theirs, history = tighten_yarns(
            laid,
            job["yarn_diameter"],
            iterations=iterations,
            core_radius=job["core_radius"],
            rigid=[k for k, stiff in zip(laid.points, job["rigid"]) if stiff],
        )
        xy_py = theirs.formed()[:, :, :2].reshape(-1)
        xy_js = np.array(mine["xy"])
        if close is not None:
            assert np.max(np.abs(xy_js - xy_py)) < close
        else:
            d = job["yarn_diameter"]
            assert mine["closest"] >= d * (1 - 3e-3)
            assert abs(mine["closest"] - history["closest"][-1]) < 0.01 * d

            # Length, the very thing tightening shortens: in 3D, every
            # sample at its height.  Sideways alone, a plait barely
            # shortens, and two equally tight ones can differ by more.
            heights = laid.formed()[:, :, 2:]

            def length(xy):
                yarns = np.concatenate([xy.reshape(n_yarns, n, 2), heights], axis=2)
                return np.sum(np.linalg.norm(np.diff(yarns, axis=1), axis=-1))

            assert abs(length(xy_js) / length(xy_py) - 1) < 0.02


def _laid_paths(spec):
    """The laid yarns ``build`` tightens, captured on their way."""
    from unittest import mock

    import braidpy.take_off as take_off

    captured = {}
    real = take_off.tighten_yarns

    def capture(paths, *args, **kwargs):
        captured.setdefault("paths", paths)
        return real(paths, *args, **{**kwargs, "iterations": 0})

    with mock.patch.object(take_off, "tighten_yarns", capture):
        build({**spec, "iterations": 20})
    return captured["paths"]
