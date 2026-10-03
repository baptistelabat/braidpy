# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Basic tests for the horn gear simulator."""

import pytest

from braidpy.horn_gear.examples import (
    tubular_braid_8,
)
from braidpy.horn_gear.model import Axial, BraidingMachine, Connection, HornGear

# ── Model ─────────────────────────────────────────────────────────────────────


def test_horn_gear_slot_count():
    with pytest.raises(ValueError):
        HornGear("bad", 1)


def test_horn_gear_direction_validation():
    with pytest.raises(ValueError):
        HornGear("bad", 4, direction=0)


def test_machine_invalid_gear_ref():
    gears = [HornGear("A", 4)]
    conns = [Connection("A", "X", 0, 0)]
    with pytest.raises(ValueError, match="unknown gear"):
        BraidingMachine(gears, conns)


def test_machine_invalid_slot_ref():
    gears = [HornGear("A", 4), HornGear("B", 4)]
    conns = [Connection("A", "B", 0, 10)]  # slot_b0=10 out of range
    with pytest.raises(ValueError, match="out of range"):
        BraidingMachine(gears, conns)


# ── Layout ────────────────────────────────────────────────────────────────────


# ── Tracks ────────────────────────────────────────────────────────────────────


# ── Simulation ────────────────────────────────────────────────────────────────


# ── Axial columns and tube cores ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "axials,message",
    [
        ([Axial("x", ("NOPE",))], "unknown gear"),
        ([Axial("x", ())], "empty anchor"),
        ([Axial("x", ("A",)), Axial("x", ("B",))], "Duplicate axial"),
    ],
)
def test_invalid_axials_are_rejected(axials, message):
    m = tubular_braid_8()
    with pytest.raises(ValueError, match=message):
        BraidingMachine(list(m.gears.values()), m.connections, axials)


# ── Examples sanity ───────────────────────────────────────────────────────────


# ── Animation continuity ───────────────────────────────────────────────────────


# ── One cycle, and round again ────────────────────────────────────────────────


# ── Jacquard lace machine ─────────────────────────────────────────────────────


GREEN, RED, GREY = "60,170,90", "205,60,55", "140,140,140"


def _disc_colours(figure_or_frame):
    """The fill of every gear disc, in gear order."""
    return [t.fillcolor for t in figure_or_frame.data if t.fill == "toself"]
