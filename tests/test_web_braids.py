# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The table of braids Braid Studio's front page lists (braidpy.web.braids)."""

from braidpy import web

# A catalogue of braids by topology, as topology_catalog.export writes it,
# of one braid made two ways.
TOPOLOGIES = [
    {
        "name": "flat3",
        "title": "Plait, or flat sinnet of 3 (ABOK 2965)",
        "fingerprint": {
            "n_strands": 3,
            "loops": [3],
            "writhe": 0,
            "linking": [],
            "alexander": [1.0],
        },
        "methods": [
            {
                "source": "word",
                "name": "flat3",
                "title": "Plait, or flat sinnet of 3 (ABOK 2965)",
                "spec": {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6},
                "links": [
                    {
                        "title": "The Ashley Book of Knots, #2965",
                        "kind": "book",
                        "url": "",
                    }
                ],
            },
            {
                "source": "sinnet",
                "name": "abok_2965",
                "title": "ABOK #2965, 3-strand sinnet",
                "spec": {"source": "sinnet", "name": "abok_2965", "cycles": 1},
                "links": [],
            },
        ],
    }
]


def test_every_braid_offered_is_a_row_once():
    rows = web.braids(TOPOLOGIES)
    assert len(rows) == len(web.premade_specs())
    assert [row["spec"] for row in rows] == [dict(s) for s in web.premade_specs()]
    assert len({row["key"] for row in rows}) == len(rows)
    assert all(row["title"] and row["source"] for row in rows)


def test_a_braid_says_what_it_is_from_its_topology():
    rows = {row["key"]: row for row in web.braids(TOPOLOGIES)}
    plait = rows["word-flat3"]
    assert (plait["n_strands"], plait["loops"], plait["writhe"]) == (3, [3], 0)
    assert plait["same"] == ["ABOK #2965, 3-strand sinnet"]
    assert plait["links"][0]["title"] == "The Ashley Book of Knots, #2965"
    # Made on Ashley's stand, the same braid, the plait among its kin.
    assert rows["sinnet-abok_2965"]["same"] == [plait["title"]]


def test_a_braid_whose_topology_is_not_known_says_nothing_of_it():
    rows = {row["key"]: row for row in web.braids(TOPOLOGIES)}
    machine = rows["machine-triaxial_16"]
    assert "n_strands" not in machine and "topology" not in machine
    # Its links come from its catalogue all the same.
    assert machine["links"][0]["kind"] == "article"
