# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid3d design read as a mobidai braid (braidpy.b3d)."""

import json
import math
import urllib.parse
from pathlib import Path

import pytest

from braidpy import web
from braidpy.b3d import mobidai_from_b3d
from braidpy.similarity import fingerprint, same_fingerprint
from braidpy.topology_catalog import braid_of

# Ashley's #3054, designed in braid3d by hand.
ABOK_3054 = Path(__file__).parent / "abok3054.b3d"


def _braid(spec):
    return braid_of(web.build(spec, tighten=False)["info"])


def _design(start, steps):
    """A braid3d file: yarns at angles in degrees, and steps of moves."""
    rad = math.radians
    return urllib.parse.quote(
        json.dumps(
            {
                "nThreads": len(start),
                "threadStates": [{"colour": 0xFF0000 + k} for k in range(len(start))],
                "steps": [
                    {
                        "type": None,
                        "moves": [],
                        "poss": [
                            {"angle": rad(a), "id": str(k)} for k, a in enumerate(start)
                        ],
                    },
                    *steps,
                ],
            }
        )
    )


def _moves(*pairs):
    rad = math.radians
    return {
        "type": "threadMove",
        "moves": [{"from": rad(a), "to": rad(b)} for a, b in pairs],
    }


def test_a_braid_designed_in_braid3d_is_the_braid_ashley_draws():
    """Ashley's #3054 as designed in braid3d — its yarns at angles of no
    regular disk, a cycle and a repeat moving them back — is, read as a
    mobidai braid, the sinnet the catalogue has from Ashley's own drawing:
    the same loops, writhe, linking and Alexander polynomial."""
    entry, cycles = mobidai_from_b3d(ABOK_3054.read_text())
    assert cycles == 11
    assert len(entry.initial_slots) == 17
    spec = web.from_b3d(ABOK_3054.read_text())
    assert spec["cycles"] == 11 and spec["n_slots"] == entry.n_slots
    assert spec["colours"].split(",")[4] == "#0019ff"
    once = _braid({**spec, "cycles": 1})
    ashley = _braid({"source": "sinnet", "name": "abok_3054", "cycles": 1})
    assert same_fingerprint(fingerprint(once), fingerprint(ashley))


def test_angles_on_a_regular_disk_are_its_slots():
    """Yarns a quarter turn apart, one moving a quarter round: a disk of
    four slots, the move from slot to slot, the short way."""
    entry, cycles = mobidai_from_b3d(_design([0, 90, 180], [_moves((90, 270))]))
    assert entry.n_slots == 4 and cycles == 1
    assert [slot for slot, _ in entry.initial_slots] == [1, 2, 3]
    assert entry.moves == ((2, 4),)


def test_a_yarn_moving_where_another_of_its_step_leaves_waits_for_it():
    """Two yarns sliding round together, listed the back one first: the one
    ahead goes first, and neither stands on the other."""
    entry, _ = mobidai_from_b3d(_design([0, 45, 180], [_moves((0, 45), (45, 90))]))
    assert entry.n_slots == 8
    assert entry.moves == ((2, 3), (1, 2))


def test_a_half_turn_goes_round_as_a_mobidai_move_does():
    """The file cannot say which way round a move of half a turn goes: it
    goes the way a mobidai's own does, up the slots."""
    entry, _ = mobidai_from_b3d(_design([0, 90], [_moves((0, 180))]))
    assert entry.moves == ((1, 3),)


@pytest.mark.parametrize(
    "text, said",
    [
        ("not a design", "not a braid3d file"),
        (urllib.parse.quote(json.dumps({"nThreads": 2})), "no yarns and steps"),
        (
            urllib.parse.quote(json.dumps({"nThreads": 2, "steps": [{"poss": []}]})),
            "nowhere to start",
        ),
        (_design([0, 90], [_moves((45, 180))]), "where no yarn is"),
    ],
)
def test_a_file_that_cannot_be_read_says_why(text, said):
    with pytest.raises(ValueError, match=said):
        mobidai_from_b3d(text)
