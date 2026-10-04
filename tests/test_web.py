# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the web page asks of braidpy, answered as plain data."""

import json
import math
import subprocess
import sys

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
        result = build(
            {"source": source, "name": entry["name"], "cycles": 1, "iterations": 5}
        )
        assert result["strands"], entry["name"]
        json.dumps(result)


def test_a_machine_over_a_core_shows_it():
    result = build(
        {"source": "machine", "name": "princess", "cycles": 1, "iterations": 5}
    )
    assert [core["name"] for core in result["cores"]] == ["Core cord"]
    assert "word" not in result["info"]


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
    """No drawing library: in a browser they would be tens of megabytes."""
    code = (
        "import sys; from braidpy.web import build, catalogue\n"
        "for source, about in catalogue().items():\n"
        "    build({'source': source, **about['defaults'], 'iterations': 1,"
        " 'cycles': 1})\n"
        "print([m for m in ('plotly', 'matplotlib', 'imageio') if m in sys.modules])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "[]"
