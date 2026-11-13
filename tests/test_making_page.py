# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What Braid Studio shows of the braid made other ways:
braidpy.making.for_page and sinnet_for_page."""

import pytest

from braidpy import Braid
from braidpy.making import for_page, sinnet_for_page
from braidpy.making.disk import DiskMoves, disk_braid
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


@pytest.mark.parametrize(
    "spec",
    [
        PLAIT,
        # Two plaits side by side, as on a line of three gears whose middle
        # one is split between them.
        {"source": "word", "word": "1 -2 4 -5", "n_strands": 6, "repeat": 3},
    ],
)
def test_braid_studio_makes_the_lace_card_it_shows(spec):
    """The lace machine shown is one the page makes, from its own address:
    the same braid comes off it, however written (braidpy.conjugacy)."""
    from braidpy.conjugacy import same_braid as proven

    lace = for_page(_info(spec))["lace"]["spec"]
    assert lace["name"] == "custom" and lace["cycles"] == spec["repeat"]
    made = build({**lace, "iterations": 0}, tighten=False)["info"]
    word = tuple(int(g) for g in made["word"].split())
    shown = tuple(int(g) for g in spec["word"].split())
    n = spec["n_strands"]
    assert made["n_strands"] == n
    assert proven(Braid(word, n), Braid(shown, n))


def test_ashley_s_stand_is_searched_for_when_asked():
    found = sinnet_for_page(_info(PLAIT))
    assert found["spec"]["counts"] == "2 1"
    assert found["spec"]["moves"] == "1>2, 2>1"
    assert found["spec"]["cycles"] == 6  # as many as the braid shown repeats


def test_a_sinnet_found_is_made_as_long_as_the_stand_takes():
    """Ashley's flat sinnet of 7 (#2968), made as many times as the braid
    shown repeats its unit -- fourteen -- or as near as the stand will take,
    which is twelve.  Asking fourteen is refused when the link is followed.
    """
    found = sinnet_for_page(
        _info(
            {"source": "word", "word": "1 2 3 -6 -5 -4", "n_strands": 7, "repeat": 14}
        )
    )
    assert found["spec"]["counts"] == "4 3"
    assert found["spec"]["cycles"] == 12
    build({**found["spec"], "iterations": 0}, tighten=False)


def test_a_braid_with_no_word_has_nothing_shown():
    # Its carriers meet two steps in: the machine stops, and reads no word.
    info = _info({"source": "machine", "name": "flat_3", "carriers": "A:1 B:2"})
    assert for_page(info) == {}
    assert sinnet_for_page(info)["spec"] is None


def test_the_twin_plait_machine_is_made_on_a_lace_machine():
    """Two plaits braided at once on a line with a split gear: its lace card
    is a link to a lace machine making the same braid."""
    from braidpy.conjugacy import same_braid as proven

    shown = _info({"source": "machine", "name": "twin_plait"})
    made = build({**for_page(shown)["lace"]["spec"], "iterations": 0}, tighten=False)

    def braid(info):
        word = tuple(int(g) for g in info["word"].split())
        return Braid(word, info["n_strands"])

    assert proven(braid(shown), braid(made["info"]))


def test_a_link_asks_for_no_more_passes_than_its_source_takes():
    """The rectangular braid of 14 repeats its unit fourteen times, where
    Ashley's stand takes twelve: the link asks for twelve and is drawn,
    rather than asking fourteen and being refused when it is followed.  The
    disk and the lace machine take fourteen, so those are left alone.
    """
    from braidpy.braid_catalog import RECTANGULAR_14
    from braidpy.web._settings import Sinnet

    spec = {"source": "word", "word": RECTANGULAR_14, "n_strands": 14, "repeat": 14}
    info = _info(spec)
    shown = for_page(info)
    assert shown["disk"]["spec"]["cycles"] == 14
    assert shown["lace"]["spec"]["cycles"] == 14
    offered = sinnet_for_page(info, time_limit=0.5)
    sinnet = offered["spec"] or offered["exact"]
    assert sinnet["cycles"] == Sinnet.cycles.high == 12
    # Followed, it makes a braid rather than being turned away.
    made = build({**sinnet, "iterations": 0}, tighten=False)
    assert made["info"]["n_strands"] == 14
