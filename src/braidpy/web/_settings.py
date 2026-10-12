# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Each source's settings, as data: what a description may give, its
default when it does not, and the bounds it must keep to.  The builders
read their settings through these, and the catalogue gives the page the
same defaults (``shown``): one place for each, kept in step."""

from __future__ import annotations

from braidpy.web._spec import Count, Number, Text

# A catalogued braid's name, for the braid typed in instead.
OWN = "custom"

# The steps tightening the yarns sideways takes, by default; 0 lays them
# without tightening them.
ITERATIONS = Count("iterations", 150, low=0, high=2000)

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
    strands_in = 4
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
