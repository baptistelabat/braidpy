# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Each source's settings, as data: what a description may give, its
default when it does not, and the bounds it must keep to.  The builders
read their settings through these, and the catalogue gives the page the
same defaults (``shown``): one place for each, kept in step."""

from __future__ import annotations

from typing import Dict, List

from braidpy.web._spec import Count, Number, Text
from braidpy.web._types import Default, Example

# A catalogued braid's name, for the braid typed in instead.
OWN = "custom"

# The steps tightening the yarns sideways takes, by default; 0 lays them
# without tightening them.
ITERATIONS = Count("iterations", 150, low=0, high=2000)

# ------------------------------------------------------------- braid words


class Word:
    """A braid word, flat or round a ring, repeated."""

    layout = Text("layout", "row")
    layouts = ("row", "ring")
    word = Text("word", "")
    # By default, as many strands as the word needs.
    n_strands = Count("n_strands", 2, low=2, high=32)
    repeat = Count("repeat", 1, low=1, high=50)
    yarn_diameter = Number("yarn_diameter", 0.45, low=0.05, high=0.95)
    most_crossings = 2000
    # Laid with so many samples a crossing; a long word with fewer, as few
    # as ``fewest_samples``: the work of laying grows as the square of them,
    # and laid it is only a first sight of the braid, made then on the
    # marudai.
    samples = 24
    samples_up_to = 100
    fewest_samples = 6
    # How it is to be settled: by physics, it is laid round a ring.
    settle = Text("settle", "")
    by_physics = ("physics", "crossing")
    # What the page starts from, and the words it offers.
    starts: Dict[str, Default] = {"word": "1 -2", "n_strands": 3, "repeat": 6}
    examples: List[Example] = [
        {"word": "1 -2", "n_strands": 3, "repeat": 6, "title": "Plait"},
        {"word": "1 2 3", "n_strands": 4, "repeat": 12, "title": "Twist"},
        {"word": "1 -2 3 -2", "n_strands": 4, "repeat": 4, "title": "Four-strand flat"},
        {"word": "1 1 1", "n_strands": 2, "repeat": 8, "title": "Two-ply"},
        {
            "layout": "ring",
            "word": "4",
            "n_strands": 3,
            "repeat": 36,
            "title": "Rope, as a ring word",
        },
    ]


# ------------------------------------------------------------- disk braids

# Every disk braid: its yarn, a fraction of the disk's radius, and the
# tightening steps it takes sideways.
DISK_YARN = Number("yarn_diameter", 0.12, low=0.02, high=0.5)
DISK_ITERATIONS = Count("iterations", 200, low=0, high=2000)


class Kumihimo:
    """Kumihimo's own moves, S and R, repeated."""

    pattern = Text("pattern", "SR")
    # Its moves take the strands in fours: top, bottom, left and right.
    n_strands = Count("n_strands", 8, low=4, high=32)
    repeat = Count("repeat", 8, low=1, high=50)
    shown = (pattern, n_strands, repeat)


class Mobidai:
    """A mobidai braid from the catalogue, or your own."""

    name = Text("name", "KONGO_8")
    cycles = Count("cycles", 6, low=1, high=40)
    # Your own: the disk's slots, and how far it turns after each cycle.
    n_slots = Count("n_slots", 32, low=3, high=128)
    shift = Count("shift", 0, low=-128, high=128)
    shown = (name, cycles)


class Sinnet:
    """An Ashley solid sinnet from the catalogue, or your own."""

    name = Text("name", "abok_3042")
    cycles = Count("cycles", 3, low=1, high=12)
    # Your own, at most.
    most_strands = 64
    shown = (name, cycles)
