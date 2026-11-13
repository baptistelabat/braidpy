# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A machine's carrier tracks, as the demo draws them and Braid Studio shows
them: on the machine to load, and in the view of it turning."""

import numpy as np

from braidpy import web
from braidpy.horn_gear.layout import compute_layout
from braidpy.horn_gear.visualization import track_curves
from braidpy.machine_catalog import CATALOGUE
from braidpy.web.machines import machine_geometry


def test_a_tubular_braid_has_a_track_each_way_round_and_a_plait_one():
    """The ring's carriers go round it both ways; the plait's all follow one
    figure of eight."""
    for name, count in [("tubular_8", 2), ("flat_3", 1)]:
        machine = CATALOGUE[name].make()
        curves = track_curves(machine, compute_layout(machine))
        assert len(curves) == count, name
        for _, points in curves:
            assert np.allclose(points[0], points[-1]), "closed"


def test_a_track_lies_under_its_carriers():
    """Every carrier's path, seen from above, keeps to some track: within a
    twentieth of a gear's radius, which the carriers leave only where they
    hand over between gears."""
    made = web.build(
        {"source": "machine", "name": "tubular_8", "cycles": 1}, tighten=False
    )
    timeline = made["timeline"]
    tracks = np.vstack([np.asarray(t["points"]) for t in timeline["tracks"]])
    near = machine_geometry("tubular_8")["gears"][0]["radius"] / 20
    for strand in timeline["strands"]:
        for point in np.asarray(strand):
            assert np.min(np.hypot(*(tracks - point).T)) < near


def test_braid_studio_draws_the_tracks_on_the_machine_to_load():
    drawn = machine_geometry("tubular_8")
    assert [t["colour"] for t in drawn["tracks"]] == ["#e41a1c", "#377eb8"]
    # In the plane the gears are drawn in, round them.
    centres = np.array([[g["x"], g["y"]] for g in drawn["gears"]])
    for track in drawn["tracks"]:
        points = np.asarray(track["points"])
        assert np.allclose(points[0], points[-1])
        nearest = np.min(
            np.hypot(*(points[:, None] - centres[None]).transpose(2, 0, 1)), axis=1
        )
        # The points are rounded to 1e-4.
        assert np.max(nearest) <= max(g["radius"] for g in drawn["gears"]) + 1e-3


def test_a_long_track_is_thinned_but_stays_closed():
    track = machine_geometry("flat_9")["tracks"][0]["points"]
    assert len(track) <= 600 + 1
    assert track[0] == track[-1]


def test_a_machine_driven_by_a_programme_has_no_tracks():
    assert machine_geometry("lace_dutch")["tracks"] == []
    made = web.build(
        {"source": "lace", "name": "lace_dutch", "cycles": 1}, tighten=False
    )
    assert "tracks" not in made["timeline"]
