# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the web page asks of braidpy, answered as plain data: what every
source shares."""

import json
import subprocess
import sys

import pytest

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


@pytest.mark.parametrize(
    "source", [s for s, about in catalogue().items() if "entries" in about]
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
