# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Disk braids for the web page: kumihimo, mobidai, sinnets."""

import math

import pytest

from braidpy.web import build, catalogue
from web_checks import check


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
    check(result, 8)
    assert "annular_word" in result["info"]


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"source": "kumihimo", "pattern": "SX"}, "S \\(swap\\)"),
        ({"source": "kumihimo", "n_strands": 6}, "multiple of four"),
        ({"source": "mobidai", "name": "nope"}, "No mobidai"),
        ({"source": "sinnet", "name": "nope"}, "No sinnet"),
    ],
)
def test_what_cannot_be_made_is_explained(spec, message):
    with pytest.raises(ValueError, match=message):
        build(spec)


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


def test_a_sinnet_disk_is_drawn_with_its_spaces():
    """Seen from above, a sinnet's disk shows its spaces as sectors: a line
    from the middle to the rim between each two, each space's number half
    way between its two lines."""
    result = build(
        {"source": "sinnet", "name": "abok_3044", "cycles": 1}, tighten=False
    )
    view = result["timeline"]
    n_spaces = len(view["slots"])
    rim, *sectors = view["outlines"]
    assert len(sectors) == n_spaces
    for line in sectors:
        (x0, y0), (x1, y1) = line[0], line[-1]
        assert math.hypot(x0, y0) == pytest.approx(0, abs=1e-6)
        assert math.hypot(x1, y1) == pytest.approx(math.hypot(*rim[0]), rel=1e-3)
    boundaries = sorted(
        math.atan2(line[-1][1], line[-1][0]) % (2 * math.pi) for line in sectors
    )
    for x, y, name in view["slots"]:
        angle = math.atan2(y, x) % (2 * math.pi)
        before = max(
            (b for b in boundaries if b < angle), default=boundaries[-1] - 2 * math.pi
        )
        after = min(
            (b for b in boundaries if b > angle), default=boundaries[0] + 2 * math.pi
        )
        assert angle == pytest.approx(
            (before + after) / 2, abs=0.3 * (after - before)
        ), name


@pytest.mark.parametrize(
    "spec",
    [
        {"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2},
        {"source": "mobidai", "name": "KONGO_8", "cycles": 2},
        {"source": "sinnet", "name": "abok_3042", "cycles": 2},
    ],
)
def test_how_many_repeats_make_it_pure_counts_its_unit(spec):
    """The repeats asked for are the braid's word, or its moves' cycle: so
    many of them, and no fewer, make a pure braid, whatever was made."""
    unit = build({**spec, "repeat": 1, "cycles": 1}, tighten=False)["info"]
    info = build(spec, tighten=False)["info"]
    assert info["pure_after"] == unit["pure_after"]
    assert info["repeated"] == ("cycle" if "cycles" in spec else "repeat")
    k = unit["pure_after"]
    again = build({**spec, "repeat": k, "cycles": k}, tighten=False)["info"]
    assert again["pure"]
    if k > 1:
        fewer = build({**spec, "repeat": k - 1, "cycles": k - 1}, tighten=False)
        assert not fewer["info"]["pure"]


@pytest.mark.parametrize(
    "spec, made",
    [
        ({"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 3}, 3),
        ({"source": "mobidai", "name": "KONGO_8", "cycles": 5}, 5),
        ({"source": "sinnet", "name": "abok_3042", "cycles": 2}, 2),
    ],
)
def test_a_braid_says_how_many_repeats_were_made(spec, made):
    """Beside how many repeats make it pure, how many were made — and so
    whether what was made is."""
    info = build(spec, tighten=False)["info"]
    assert info.get("made") == made
    if made:
        assert info["pure"] == (made % info["pure_after"] == 0)


@pytest.mark.parametrize("source", ["kumihimo", "mobidai", "sinnet"])
def test_a_disk_braid_made_from_its_catalogue_defaults_is_made_by_default(source):
    """The page starts from the catalogue's defaults; a description that
    gives none of them makes the same braid: both read one table."""
    given = build(
        {"source": source, **catalogue()[source]["defaults"], "iterations": 1},
        tighten=False,
    )
    assumed = build({"source": source, "iterations": 1}, tighten=False)
    assert given == assumed
