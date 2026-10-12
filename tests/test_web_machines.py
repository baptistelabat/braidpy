# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Horn gear braiding machines for the web page."""

import json

import pytest

from braidpy.web import build


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


def test_cores_are_yarn_or_rigid():
    with pytest.raises(ValueError, match="yarn or rigid"):
        build({"source": "machine", "name": "soutache_5", "cores": "glass"})


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"source": "machine", "name": "nope"}, "No machine"),
    ],
)
def test_what_cannot_be_made_is_explained(spec, message):
    with pytest.raises(ValueError, match=message):
        build(spec)


def test_a_machine_has_no_disk_to_turn_with():
    """A machine's braid does not hang from a disk: nothing turns it."""
    machine = build(
        {"source": "machine", "name": "flat_3", "cycles": 1, "iterations": 5}
    )
    assert "turn" not in machine["timeline"]


@pytest.mark.parametrize(
    "spec, made",
    [
        ({"source": "machine", "name": "tubular_8", "cycles": 1}, None),
        ({"source": "machine", "name": "flat_3", "cycles": 2}, 2),
    ],
)
def test_a_braid_says_how_many_repeats_were_made(spec, made):
    """Beside how many repeats make it pure, how many were made — and so
    whether what was made is."""
    info = build(spec, tighten=False)["info"]
    assert info.get("made") == made
    if made:
        assert info["pure"] == (made % info["pure_after"] == 0)


def test_a_machine_is_drawn_for_the_page_to_load_by_hand():
    """Its gears, where their slots are, and its own loading."""
    from braidpy.web import machine_geometry
    from braidpy.web.machines import _machines

    shape = machine_geometry("tubular_8")
    json.dumps(shape)
    assert {g["name"] for g in shape["gears"]} == {"A", "B", "C", "D"}
    for gear in shape["gears"]:
        assert {"x", "y", "radius", "ride", "slots", "direction", "offset"} <= set(gear)
    assert shape["contacts"]
    own = _machines()["tubular_8"]().default_carriers()
    assert shape["loading"] == [list(own[k]) for k in sorted(own)]


def test_a_machine_loaded_by_hand():
    """Its carriers given as gear:slot: its own loading is the same braid; a
    carrier fewer, a yarn fewer."""
    from braidpy.web import machine_geometry

    loading = machine_geometry("flat_9")["loading"]
    text = " ".join(f"{g}:{s}" for g, s in loading)
    spec = {"source": "machine", "name": "flat_9", "cycles": 1}
    own = build(spec, tighten=False)
    same = build({**spec, "carriers": text}, tighten=False)
    assert same["info"] == own["info"]
    fewer = build({**spec, "carriers": " ".join(text.split()[1:])}, tighten=False)
    assert len(fewer["strands"]) == len(own["strands"]) - 1


def test_carriers_that_meet_stop_the_braiding():
    """Two carriers meeting stops the machine: the braid is made up to there,
    and the note says where."""
    from braidpy.web import machine_geometry

    loading = machine_geometry("flat_9")["loading"]
    # One carrier more, on A:1, meets another four steps on.
    crowded = " ".join(f"{g}:{s}" for g, s in loading) + " A:1"
    result = build(
        {"source": "machine", "name": "flat_9", "cycles": 2, "carriers": crowded},
        tighten=False,
    )
    assert any("stopped" in note for note in result["notes"])
    assert result["info"]["collision"]["step"] == 4
    # Ringed where they started, the one added among them.
    assert ["A", 1] in result["info"]["collision"]["at"]
    assert len(result["strands"]) == len(loading) + 1


def test_carriers_that_meet_at_once_cannot_be_braided():
    with pytest.raises(ValueError, match="meet as soon as"):
        build(
            {"source": "machine", "name": "tubular_8", "carriers": "A:0 D:0"},
            tighten=False,
        )


@pytest.mark.parametrize(
    "carriers, message",
    [
        ("A:0 A:0", "same"),
        ("Z:0", "No gear"),
        ("A:99", "slot"),
        ("A0", "gear:slot"),
        ("none", "at least one"),
    ],
)
def test_a_loading_that_cannot_be_braided_says_so(carriers, message):
    with pytest.raises(ValueError, match=message):
        build(
            {"source": "machine", "name": "tubular_8", "carriers": carriers},
            tighten=False,
        )
