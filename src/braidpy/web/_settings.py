# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Each source's settings, as data: what a description may give, its
default when it does not, and the bounds it must keep to.  The builders
read their settings through these, and the catalogue gives the page the
same defaults (``shown``): one place for each, kept in step."""

from __future__ import annotations

from typing import Dict

from braidpy.web._spec import Colours, Count, Number, Text
from braidpy.web._types import Default

# A catalogued braid's name, for the braid typed in instead.
OWN = "custom"

# The steps tightening the yarns sideways takes, by default; 0 lays them
# without tightening them.
ITERATIONS = Count("iterations", 150, low=0, high=2000)

# The colours chosen for the strands, whatever made the braid.  Every braid
# can be recoloured, so this belongs to none of the sources in particular.
COLOURS = Colours("colours")

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
    # What the page starts from; the words it offers are
    # braidpy.braid_catalog.word_examples().
    starts: Dict[str, Default] = {"word": "1 -2", "n_strands": 3, "repeat": 6}


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


# ------------------------------------------------------------------ machines


class Machine:
    """A horn gear braiding machine, run so many cycles, its cores of yarn or
    rigid; loaded as it loads itself, unless ``carriers`` says otherwise."""

    name = Text("name", "tubular_8")
    cycles = Count("cycles", 2, low=1, high=8)
    cores = Text("cores", "yarn")
    stiffness = ("yarn", "rigid")
    # By default, a fifth of a gear radius: a plausible yarn.
    yarn_diameter = Number("yarn_diameter", 0.2, low=0.01, high=10.0)
    of_gear_radius = 0.2
    core_colour = "#8a857c"
    shown = (name, cores, cycles)


class Lace:
    """A Jacquard lace machine, its card run so many passes; threaded as it
    is, unless ``carriers`` says otherwise.  Yarns are a fifth of a gear
    radius, as on a horn gear machine (:class:`Machine`)."""

    name = Text("name", "lace_dutch")
    cycles = Count("cycles", 6, low=1, high=24)
    # Your own card: the gears round the ring, an even number, and per step
    # the gears turning anticlockwise, then clockwise, as 0 and 1.
    n_gears = Count("n_gears", 6, low=4, high=32)
    card = Text("card", "")
    shown = (name, cycles)
