# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The 2D braid diagram braidpy draws for itself.

The diagram replaced one drawn by `braid-visualiser`, and the reason was
colour: a strand was one colour in the console and another in the plot.  So
the test that matters most is that the two palettes now agree.  After that it
is the breaks — a diagram is only readable as a braid because the strand
passing behind is interrupted.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from braidpy.braid import Braid  # noqa: E402
from braidpy.braid_diagram import (  # noqa: E402
    DIAGRAM_COLORS,
    diagram_segments,
    draw_diagram,
    sample_period,
    strand_color,
)
from braidpy.parametric_strand import LINEAR, SMOOTHSTEP, strand_paths  # noqa: E402
from braidpy.utils import terminal_colors  # noqa: E402


# ── Colour: the reason the diagram is drawn here at all ───────────────────────


def test_the_diagram_uses_the_same_palette_as_the_console():
    """Same colours, same order, so a strand looks the same in both."""
    assert list(DIAGRAM_COLORS) == list(terminal_colors)
    for index, console in terminal_colors.items():
        if console.startswith("rgb("):
            continue  # a plotly spelling, translated below
        assert DIAGRAM_COLORS[index] == console


def test_every_colour_is_one_matplotlib_can_actually_draw():
    """terminal_colors carries a plotly colour string that matplotlib cannot.

    `rgb(0,128,128)` is fine for plotly and for the console, and is not a
    colour matplotlib knows, so it has to be translated rather than passed
    through.  This is the test that catches a new entry being added raw.
    """
    for colour in DIAGRAM_COLORS.values():
        assert mcolors.is_color_like(colour), f"{colour!r} is not drawable"


def test_colours_repeat_once_there_are_more_strands_than_colours():
    assert strand_color(0) == strand_color(len(DIAGRAM_COLORS))
    assert strand_color(3) == DIAGRAM_COLORS[3]


# ── Breaks: what makes it read as a braid ─────────────────────────────────────


def test_each_crossing_breaks_exactly_one_strand():
    """A crossing hides the strand that passes behind, and only that one.

    Count the breaks rather than inspect the picture: a strand drawn in two
    pieces was interrupted once.
    """
    for generators, n_strands in [([1], 2), ([1, -2, 1], 3), ([1, 2, -3], 4)]:
        braid = Braid(generators, n_strands=n_strands)
        pieces = diagram_segments(strand_paths(braid, profile=SMOOTHSTEP))
        breaks = sum(len(runs) - 1 for runs in pieces if runs)
        assert breaks == len(generators), f"{generators} gave {breaks} breaks"


def test_a_braid_with_no_crossings_is_drawn_unbroken():
    braid = Braid([0, 0], n_strands=3)
    pieces = diagram_segments(strand_paths(braid, profile=SMOOTHSTEP))
    assert all(len(runs) == 1 for runs in pieces)


def test_a_wider_gap_does_not_remove_more_strands_than_there_are():
    """The break widens with `gap`, but never swallows a whole strand."""
    braid = Braid([1, -2, 1], n_strands=3)
    strands = strand_paths(braid, profile=SMOOTHSTEP)
    narrow = diagram_segments(strands, gap=0.1)
    wide = diagram_segments(strands, gap=0.6)
    assert all(runs for runs in narrow)
    assert all(runs for runs in wide)
    narrow_drawn = sum(len(run) for runs in narrow for run in runs)
    wide_drawn = sum(len(run) for runs in wide for run in runs)
    assert wide_drawn < narrow_drawn


def test_the_strand_in_front_is_the_one_left_whole():
    """At a positive crossing the strand from the lower slot passes in front.

    Checked through the drawing rather than asserted: the strand that keeps
    its first sample through the crossing is the one not broken there.
    """
    braid = Braid([1], n_strands=2)
    strands = strand_paths(braid, profile=SMOOTHSTEP)
    pieces = diagram_segments(strands)
    whole = [index for index, runs in enumerate(pieces) if len(runs) == 1]
    broken = [index for index, runs in enumerate(pieces) if len(runs) > 1]
    assert len(whole) == 1 and len(broken) == 1
    depths = [
        max(point[1] for point in sample_period(strand, 200)) for strand in strands
    ]
    assert depths[whole[0]] > depths[broken[0]]


# ── Drawing ───────────────────────────────────────────────────────────────────


def test_it_draws_and_can_be_saved(tmp_path):
    target = tmp_path / "diagram.png"
    draw_diagram(Braid([1, -2, 1], n_strands=3), save=str(target))
    assert target.is_file() and target.stat().st_size > 0
    plt.close("all")


def test_plot_returns_the_braid_so_calls_can_be_chained():
    braid = Braid([1, -2], n_strands=3)
    assert braid.plot() is braid
    plt.close("all")


def test_a_single_colour_overrides_the_palette():
    _, ax = plt.subplots()
    draw_diagram(Braid([1, -2, 1], n_strands=3), color="black", ax=ax)
    assert {line.get_color() for line in ax.lines} == {"black"}
    plt.close("all")


@pytest.mark.parametrize("generators,n_strands", [([1], 2), ([1, 5, -3, 0], 7)])
def test_every_strand_is_drawn(generators, n_strands):
    _, ax = plt.subplots()
    draw_diagram(Braid(generators, n_strands=n_strands), ax=ax)
    assert len({line.get_color() for line in ax.lines}) == n_strands
    plt.close("all")


def test_braidpy_no_longer_needs_braid_visualiser():
    """The dependency this work exists to remove."""
    import braidpy.braid as module

    assert not hasattr(module, "bv")
    assert "braidvisualiser" not in (
        __import__("pathlib").Path("pyproject.toml").read_text()
    )


# ── How it reads: down the page, with its word ────────────────────────────────


def test_the_braid_runs_down_the_page():
    """A braid hangs downward and is worked downward, so it is drawn so.

    Checked through the axis rather than by eye: the vertical axis is
    inverted, so larger values of the braid's own coordinate are lower.
    """
    _, ax = plt.subplots()
    draw_diagram(Braid([1, -2, 1], n_strands=3), ax=ax)
    bottom, top = ax.get_ylim()
    assert bottom > top, "the braid is drawn upside down"
    plt.close("all")


def test_the_word_is_written_above_the_braid():
    _, ax = plt.subplots()
    braid = Braid([1, -2, 1], n_strands=3)
    draw_diagram(braid, ax=ax)
    assert braid.format() in ax.get_title()
    plt.close("all")


def test_the_title_can_be_replaced_or_dropped():
    _, ax = plt.subplots()
    draw_diagram(Braid([1], n_strands=2), title="", ax=ax)
    assert ax.get_title() == ""
    draw_diagram(Braid([1], n_strands=2), title="a plait", ax=ax)
    assert ax.get_title() == "a plait"
    plt.close("all")


def test_a_crossing_is_a_curve_not_a_corner():
    """Smoothstep by default, so a strand eases across rather than turning.

    The two profiles differ in where a strand is halfway through a crossing:
    linear has covered half the distance, smoothstep rather less.
    """
    braid = Braid([1], n_strands=2)
    smooth = strand_paths(braid, profile=SMOOTHSTEP)[0]
    straight = strand_paths(braid, profile=LINEAR)[0]
    quarter_way = 0.25 * smooth.length
    assert smooth.position(quarter_way)[0] < straight.position(quarter_way)[0]


def test_the_end_of_a_period_does_not_jump_back_to_the_start():
    """position() is periodic, so the last sample would otherwise wrap.

    A strand that ends in slot 2 must be drawn ending there, not snapping
    back to slot 0 for its final point.
    """
    path = strand_paths(Braid([1], n_strands=2), profile=SMOOTHSTEP)[0]
    points = sample_period(path, 50)
    assert points[-1][0] == pytest.approx(path.slots[-1] * path.spacing)
    assert abs(points[-1][0] - points[-2][0]) < 0.5 * path.spacing
