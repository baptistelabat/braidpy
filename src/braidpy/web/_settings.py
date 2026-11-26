# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Each source's settings, as data: what a description may give, its
default when it does not, and the bounds it must keep to.  The builders
read their settings through these, and the catalogue gives the page the
same defaults (``shown``): one place for each, kept in step."""

from __future__ import annotations

from typing import ClassVar

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

# The longest braid word a shorter one is looked for, in crossings, for the
# info card of any braid (braidpy.shortening): a second or so in a browser.
MOST_CROSSINGS_SHORTENED = 300

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
    starts: ClassVar[dict[str, Default]] = {"word": "1 -2", "n_strands": 3, "repeat": 6}


# ------------------------------------------------------------------- cores

# The core a braid is made round: as whatever makes it is built (a
# machine's own cores, of yarn); none; or one of yarn or rigid — a machine's
# own, or one down the hole of a ring of gears.
CORE = Text("core", "own")
CORE_KINDS = ("own", "none", "yarn", "rigid")
CORE_COLOUR = "#8a857c"
# Links made before: the stiffness, yarn or rigid, of a machine's own cores.
OLD_CORES = Text("cores", "yarn")
# A disk has no core of its own: none, or one down its middle.
DISK_CORE = Text("core", "none")
DISK_CORE_KINDS = ("none", "yarn", "rigid")

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
    core = DISK_CORE
    shown = (pattern, n_strands, repeat, core)


class Mobidai:
    """A mobidai braid from the catalogue, or your own."""

    name = Text("name", "KONGO_8")
    cycles = Count("cycles", 6, low=1, high=40)
    # Your own: the disk's slots, and how far it turns after each cycle.
    n_slots = Count("n_slots", 32, low=3, high=128)
    shift = Count("shift", 0, low=-128, high=128)
    core = DISK_CORE
    shown = (name, cycles, core)


class Sinnet:
    """An Ashley solid sinnet from the catalogue, or your own."""

    name = Text("name", "abok_3042")
    cycles = Count("cycles", 3, low=1, high=12)
    # Your own, at most.
    most_strands = 64
    shown = (name, cycles)


class Shape:
    """A sinnet from the shape it is to take, as Ashley draws it
    (:mod:`braidpy.making.ashley`): its grid, a shape to start from on it
    and its size, in lines, or its own cells; the order of the moves; the
    tracks made the other way round, by number; and the spaces given a
    strand more, by number, a space named twice given two, and the strands
    added at each corner."""

    grid = Text("grid", "triangle")
    shape = Text("shape", "triangle")
    size = Count("size", 4, low=2, high=12)
    height = Count("height", 2, low=2, high=12)
    cells = Text("cells", "")
    order = Text("order", "book")
    turned = Text("turned", "")
    extra = Text("extra", "")
    corners = Count("corners", 0, low=0, high=3)
    cycles = Count("cycles", 3, low=1, high=12)
    most_strands = Sinnet.most_strands
    # The grids (making.ashley.GRIDS) and the shapes to start from on each
    # (making.ashley.grid_shape), and the orders of the moves
    # (making.ashley.ORDERS), with their titles.
    grids: ClassVar[dict[str, str]] = {
        "square": "Square: lines at 0° and 90°",
        "diagonal": "Diamond: lines at 0° and 90°, sides at 45° too",
        "triangle": "Triangular: lines at 0°, 60° and 120°",
        "skew": "Skewed: lines at 0° and 120°, and at 60° between their crossings",
    }
    shapes: ClassVar[dict[str, dict[str, str]]] = {
        "square": {
            "oblong": "Oblong",
            "L": "L",
            "U": "U",
            "frame": "Hollow square",
        },
        "diagonal": {"square": "Square", "oblong": "Oblong"},
        "triangle": {"triangle": "Triangle", "hexagon": "Hexagon"},
        "skew": {
            "oblong": "Parallelogram",
            "L": "L",
            "U": "U",
            "frame": "Hollow rhomb",
        },
    }
    orders: ClassVar[dict[str, str]] = {
        "book": "The book's, alternating",
        "spaces": "Space by space",
    }
    shown = (grid, shape, size, height, order, corners, cycles)
    # What makes the braid what it is: two descriptions alike in these are
    # of one braid (braidpy.topology_catalog).
    defining = (grid, shape, size, height, cells, order, turned, extra, corners)
    # Braids made so, offered as they come, each as it is described.
    # Braids made so, offered as they come, each as it is described,
    # after the book's that a shape draws (solid_sinnets_catalog.DRAWN).
    examples: ClassVar[list[dict[str, Default]]] = [
        {
            "title": "Hexagon, 3 lines a side",
            "grid": "triangle",
            "shape": "hexagon",
            "size": 3,
        },
        {
            "title": "Square, 4 lines a side",
            "grid": "square",
            "shape": "oblong",
            "size": 4,
            "height": 4,
        },
        {
            "title": "Parallelogram, 4 by 6 lines, #3078 made larger",
            "grid": "skew",
            "shape": "oblong",
            "size": 4,
            "height": 6,
        },
        {
            "title": "Parallelogram, 3 by 8 lines, #3078 made longer",
            "grid": "skew",
            "shape": "oblong",
            "size": 3,
            "height": 8,
        },
        {
            "title": "L, 5 lines, its arms 2 thick",
            "grid": "square",
            "shape": "L",
            "size": 5,
            "height": 2,
        },
        {
            "title": "U, 6 lines, its arms 2 thick",
            "grid": "square",
            "shape": "U",
            "size": 6,
            "height": 2,
        },
        {
            "title": "Hollow square, 6 lines, its sides 2 thick",
            "grid": "square",
            "shape": "frame",
            "size": 6,
            "height": 2,
        },
        {
            "title": "Hollow square, 7 lines, its sides 3 thick",
            "grid": "square",
            "shape": "frame",
            "size": 7,
            "height": 3,
        },
    ]


# ------------------------------------------------------------------ machines


class Machine:
    """A horn gear braiding machine, run so many cycles, round the core
    asked for (``CORE``); loaded as it loads itself, unless ``carriers``
    says otherwise."""

    name = Text("name", "tubular_8")
    cycles = Count("cycles", 2, low=1, high=8)
    core = CORE
    # By default, a fifth of a gear radius: a plausible yarn.
    yarn_diameter = Number("yarn_diameter", 0.2, low=0.01, high=10.0)
    of_gear_radius = 0.2
    # The bobbins it carries, in mm: the machine is sized so that the two
    # carriers coming closest still pass (braidpy.horn_gear.take_off
    # .Clearance), and its size said in a note.
    bobbin_diameter_mm = Number("bobbin_diameter_mm", 20.0, low=1.0, high=500.0)
    # How it is to be settled: by its carriers (Carried).
    settle = Text("settle", "")
    # Your own: the gears that mesh, as A-B B-C, and the slots of a gear
    # the graph does not give its own (braidpy.horn_gear.described).
    graph = Text("graph", "")
    n_slots = Count("n_slots", 4, low=2, high=24)
    # Where it feeds axial yarns, as B or A-B-C-D: its own if not given,
    # none if "none" (braidpy.horn_gear.described.read_axials).
    axials = Text("axials", "")
    no_axials = "none"
    shown = (name, core, cycles)


class Carried:
    """A machine's braid made by its carriers going round, in the page
    (braidpy.carried, web/carried.js): asked for as how to settle it."""

    settle = "carriers"
    # The most steps of the machine it is made over: a step takes about a
    # second for a few carriers, in the page.
    most_steps = 24


class Lace:
    """A Jacquard lace machine, its card run so many passes; threaded as it
    is, unless ``carriers`` says otherwise.  Yarns are a fifth of a gear
    radius, as on a horn gear machine (:class:`Machine`)."""

    name = Text("name", "lace_dutch")
    cycles = Count("cycles", 6, low=1, high=24)
    # Your own card: the gears round the ring, an even number, and per step
    # the gears turning anticlockwise, then clockwise, as 0 and 1.
    # As many gears as the largest lace machines have, 72.
    n_gears = Count("n_gears", 6, low=4, high=72)
    card = Text("card", "")
    # How it is to be settled: on a marudai, made from its card alone.
    settle = Text("settle", "")
    core = CORE
    shown = (name, core, cycles)
