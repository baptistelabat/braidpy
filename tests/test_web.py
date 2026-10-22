# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the web page asks of braidpy, answered as plain data: what every
source shares."""

import json
import subprocess
import sys

import pytest

from braidpy.web._settings import COLOURS
from braidpy.web import build, catalogue


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


# Every sinnet, the biggest of 36 strands, takes minutes: run daily.
@pytest.mark.parametrize(
    "source",
    [
        pytest.param(s, marks=pytest.mark.slow) if s == "sinnet" else s
        for s, about in catalogue().items()
        if "entries" in about
    ],
)
def test_every_catalogue_entry_is_made(source):
    for entry in catalogue()[source]["entries"]:
        if entry["name"] == "custom":
            continue  # made from what is typed in: see below
        result = build(
            {"source": source, "name": entry["name"], "cycles": 1, "iterations": 5}
        )
        assert result["strands"], entry["name"]
        json.dumps(result)


def test_the_catalogue_is_plain_data_with_defaults():
    entries = catalogue()
    json.dumps(entries)
    for source, about in entries.items():
        build({"source": source, **about["defaults"], "iterations": 1, "cycles": 1})


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"source": "nowhere"}, "Unknown source"),
        ({"source": "kumihimo", "yarn_diameter": "thick"}, "number"),
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


def test_the_catalogue_is_listed_before_any_machine_is_loaded():
    """The page lists the catalogue as soon as braidpy is in, and only loads
    networkx, for the machines, once one is asked for."""
    code = (
        "import json, sys; from braidpy.web import catalogue\n"
        "json.dumps(catalogue())\n"
        "print('networkx' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False"


@pytest.mark.parametrize("source", sorted(catalogue()))
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


@pytest.mark.parametrize(
    "spec",
    [
        {"source": "machine", "name": "flat_9", "cycles": 1},
        {"source": "machine", "name": "tubular_8", "cycles": 1},
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 3},
    ],
    ids=lambda spec: spec.get("name") or spec["word"],
)
def test_a_braid_forms_on_a_fell_ring_not_a_point(spec):
    """A braid forms on a ring about its own size, yarns being as thick as
    they are: a machine's braid and a braid word in a row are laid so, every
    two yarns a diameter apart at the fell, not drawn in to one point."""
    import itertools

    import numpy as np

    result = build({**spec, "iterations": 0})
    fell = [min(s["points"], key=lambda p: p[2]) for s in result["strands"]]
    apart = min(
        float(np.hypot(p[0] - q[0], p[1] - q[1]))
        for p, q in itertools.combinations(fell, 2)
    )
    assert apart > 0.99 * result["yarn_diameter"]


# ── colours chosen by hand ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "given, want",
    [
        (["#e41a1c", "#377EB8"], ("#e41a1c", "#377eb8")),
        ("#e41a1c,#377eb8", ("#e41a1c", "#377eb8")),
        ("#e41a1c, ,#4daf4a", ("#e41a1c", None, "#4daf4a")),
        ("#f00", ("#f00",)),
        ("", ()),
        (None, ()),
    ],
)
def test_colours_are_read_however_they_are_written(given, want):
    """A list, or one string of them, which is what fits in a link."""
    assert COLOURS.read({} if given is None else {"colours": given}) == want


@pytest.mark.parametrize("given", ["red", "#12345", "#gggggg", "e41a1c"])
def test_colours_that_cannot_be_read_say_so(given):
    with pytest.raises(ValueError, match="not a colour"):
        COLOURS.read({"colours": given})


def test_a_chosen_colour_replaces_the_one_the_braid_was_made_with():
    spec = {"source": "word", "word": "1 -2", "n_strands": 3, "iterations": 0}
    made = build(dict(spec))
    chosen = build(dict(spec, colours="#112233,,#445566"))
    assert [s["colour"] for s in chosen["strands"]] == [
        "#112233",
        made["strands"][1]["colour"],
        "#445566",
    ]


def test_choosing_a_colour_changes_nothing_else_about_the_braid():
    """Only what the strands are painted with: the braid is the same braid."""
    spec = {"source": "word", "word": "1 -2", "n_strands": 3, "iterations": 0}
    made = build(dict(spec))
    chosen = build(dict(spec, colours="#112233"))
    for before, after in zip(made["strands"], chosen["strands"]):
        assert before["points"] == after["points"]
        assert before["name"] == after["name"]
    assert made["info"] == chosen["info"]


def test_more_colours_than_strands_are_no_trouble():
    spec = {"source": "word", "word": "1 -2", "n_strands": 3, "iterations": 0}
    chosen = build(dict(spec, colours=",".join(["#010101"] * 9)))
    assert [s["colour"] for s in chosen["strands"]] == ["#010101"] * 3


@pytest.mark.parametrize("source", ["word", "kumihimo", "machine"])
def test_every_kind_of_braid_can_be_recoloured(source):
    """Whatever chose the colours to start with, a page may choose its own."""
    starts = {
        "word": {"word": "1 -2", "n_strands": 3},
        "kumihimo": {"pattern": "SR", "n_strands": 8, "repeat": 1},
        "machine": {"name": "tubular_8", "cycles": 1},
    }
    spec = {"source": source, "iterations": 0, **starts[source]}
    chosen = build(dict(spec, colours="#0a0b0c"))
    assert chosen["strands"][0]["colour"] == "#0a0b0c"


def test_every_braid_offered_as_it_comes_is_made_with_the_site():
    """Each catalogued braid and braid word example, nothing of your own."""
    from braidpy.web import premade_specs

    specs = premade_specs()
    listed = catalogue()
    for source, about in listed.items():
        for entry in about.get("entries", []):
            wanted = {"source": source, "name": entry["name"]}
            assert (wanted in specs) == (entry["name"] != "custom")
    for example in listed["word"]["examples"]:
        assert {
            "source": "word",
            **{k: v for k, v in example.items() if k != "title"},
        } in specs


def test_a_braid_made_with_the_site_is_the_braid_made_for_the_page(
    tmp_path, monkeypatch
):
    """Written as build lays it for a page to tighten, and said in the
    index; the same every time it is made."""
    import braidpy.web as web

    specs = [
        {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6},
        {"source": "sinnet", "name": "abok_2965"},
        {"source": "sinnet", "name": "no_such_sinnet"},
    ]
    monkeypatch.setattr(web, "premade_specs", lambda: specs)
    index = web.premade(str(tmp_path), workers=1)
    assert [entry["spec"] for entry in index] == specs[
        :2
    ]  # what cannot be made is left out
    assert json.loads((tmp_path / "index.json").read_text()) == index
    for entry in index:
        written = json.loads((tmp_path / entry["file"]).read_text())
        assert written == json.loads(json.dumps(build(entry["spec"], tighten=False)))
    again = web.premade(str(tmp_path / "again"), workers=1)
    for entry in again:
        assert (tmp_path / "again" / entry["file"]).read_text() == (
            tmp_path / entry["file"]
        ).read_text()
