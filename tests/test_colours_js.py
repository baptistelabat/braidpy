# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/colours.js: the colours chosen by hand, as a braid's link carries them."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "colours_cases.mjs"


@pytest.fixture(scope="module")
def out():
    run = subprocess.run(
        ["node", str(CASES)], capture_output=True, text=True, check=True
    )
    return json.loads(run.stdout)


def test_colours_chosen_on_a_longer_braid_leave_the_link_of_a_shorter_one(out):
    """Strands 2, 5, 17 and 19 coloured on a braid of twenty, then a braid of
    sixteen made: its link names its own strands' colours only, not twenty."""
    assert len(out["chosenOnTwenty"].split(",")) == 20
    assert out["letGo"] is False
    assert out["letGoOnSixteen"] is True
    assert out["chosenOnSixteen"] == ",,#ff0000,,,#00ff00"
    assert out["letGoAgain"] is False


def test_empty_places_after_the_last_colour_are_not_written(out):
    assert out["trailing"] == "#ff0000"
    assert out["none"] == ""
