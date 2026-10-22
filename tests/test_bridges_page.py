# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What Braid Studio shows of the braid made other ways:
braidpy.bridges.for_page and sinnet_for_page."""

from braidpy import Braid
from braidpy.bridges import for_page, sinnet_for_page
from braidpy.bridges.disk import DiskMoves, disk_braid
from braidpy.ring_program import same_braid
from braidpy.web import build


def _info(spec):
    return build({**spec, "iterations": 0}, tighten=False)["info"]


PLAIT = {"source": "word", "word": "1 -2", "n_strands": 3, "repeat": 6}


def test_the_plait_shown_as_a_disk_and_a_lace_card():
    shown = for_page(_info(PLAIT))
    assert shown["crossings"] == 2  # its repeating unit
    disk = shown["disk"]
    assert disk["spec"]["cycles"] == 6  # as many as the braid shown repeats
    moves = DiskMoves(
        32,
        tuple(int(s) for s in disk["spec"]["slots"].split()),
        tuple(tuple(int(p) for p in m.split(">")) for m in disk["moves"].split(", ")),
    )
    assert same_braid(disk_braid(moves), Braid((1, -2), 3))
    lace = shown["lace"]
    assert lace["gears"] == 4 and lace["threading"] == "A-B B-C C-D"
    # The gears named, then two lines a step: anticlockwise, then clockwise.
    assert len(lace["card"].splitlines()) == 1 + 2 * lace["steps"]


def test_braid_studio_makes_what_it_shows():
    made = build({**for_page(_info(PLAIT))["disk"]["spec"], "iterations": 0})
    word = tuple(int(g) for g in made["info"]["word"].split())
    assert Braid(word, 3) == Braid((1, -2) * 6, 3)


def test_ashley_s_stand_is_searched_for_when_asked():
    found = sinnet_for_page(_info(PLAIT))
    assert found["spec"]["counts"] == "2 1"
    assert found["spec"]["moves"] == "1>2, 2>1"
    assert found["spec"]["cycles"] == 6  # as many as the braid shown repeats


def test_a_sinnet_found_is_made_as_long_as_the_braid_shown():
    """Ashley's flat sinnet of 7 (#2968), made as many times as the braid."""
    found = sinnet_for_page(
        _info(
            {"source": "word", "word": "1 2 3 -6 -5 -4", "n_strands": 7, "repeat": 14}
        )
    )
    assert found["spec"]["counts"] == "4 3"
    assert found["spec"]["cycles"] == 14


def test_a_braid_with_no_word_has_nothing_shown():
    info = _info({"source": "machine", "name": "soutache_5"})
    assert for_page(info) == {}
    assert sinnet_for_page(info)["spec"] is None
