"""Generate the braid geometry demo pages.

Two kinds of page, and the difference between them matters:

- for a flat braid, the curve braidpy *draws* through the braid word, with
  its exact Fourier series laid over it and its spectrum.  A drawing, not the
  shape a strand would take under tension.
- for a rope and for the classic plait, the shape itself — the cases where
  symmetry makes one available.  Each gets a line drawing and a second page
  with the strands drawn as yarn at their real thickness, where the touching
  that sets the braid's size can actually be seen.

See docs/source/why_no_closed_form.md for why there is no third kind.

Run from the repository root: ``python gen_braid_geometry_demo.py``
"""

import math
import sys

sys.path.insert(0, "src")

from braidpy.annulus_braid import (  # noqa: E402
    lay_radius,
    cover_factor,
    crossing_binds_above,
    radius_for_cover,
    tubular_braid,
    tubular_braid_clearance,
    tubular_braid_radius,
    minimum_lay,
    packing_radius,
    rope_helices,
)
from braidpy.braid import Braid  # noqa: E402
from braidpy.parametric_braid import ParametricBraid, closest_approach  # noqa: E402
from braidpy.parametric_strand import (  # noqa: E402
    SMOOTHSTEP,
    strand_paths,
)
from braidpy.pure_braid import closing_repeats  # noqa: E402
from braidpy.symmetric_braid import (  # noqa: E402
    braid_word,
    figure_eight_clearance,
    figure_eight_strands,
    tightest_figure_eight,
)

# (name, one repeat of the word, strands, harmonics to draw, title)
BRAIDS = [
    ("flat_3", (1, -2), 3, 6, "Flat braid \u2013 3 strands"),
    ("twist_3", (1, 2), 3, 6, "Three strands, every crossing the same way"),
    ("flat_4", (1, -2, 3, -2), 4, 8, "Flat braid \u2013 4 strands"),
    ("pure_2", (1, 1), 2, 6, "Pure braid \u2013 2 strands twisted twice"),
]

# (name, strands, title) \u2014 the shape, not a drawing of it
ROPES = [
    ("rope_3", 3, "Rope \u2013 3 strands laid up"),
    ("rope_4", 4, "Rope \u2013 4 strands laid up"),
    ("rope_7", 7, "Rope \u2013 7 strands laid up"),
]

# (name, period as a multiple of the diameter, title) \u2014 also a shape
PLAITS = [
    ("plait_tight", 3, 8.0, "Flat braid \u2013 3 strands, as tight as it goes"),
    ("plait_easy", 3, 20.0, "Flat braid \u2013 3 strands, laid out long"),
    (
        "plait_5",
        5,
        12.0,
        "Five-strand figure-eight braid, as tight as it goes "
        "(<i>not</i> the classical flat sinnet \u2014 see braid_sinnet_5)",
    ),
    (
        "plait_5_long",
        5,
        24.0,
        "Five-strand figure-eight braid, laid out long",
    ),
]


def drawn_braids() -> None:
    """The curve braidpy draws through a braid word.

    A drawing, in the convention `strand_paths` implements — not the shape a
    strand would take under tension.  See
    docs/source/why_no_closed_form.md.
    """
    for name, once, n_strands, _harmonics, title in BRAIDS:
        repeats = closing_repeats(Braid(once, n_strands=n_strands))
        braid = Braid(once * repeats, n_strands=n_strands)
        paths = strand_paths(braid, profile=SMOOTHSTEP)

        ParametricBraid([path.to_parametric() for path in paths]).plot(
            n_sample=600,
            title=f"{title} \u2014 {len(once)} generators repeated {repeats}x to "
            f"close. A drawing, not a shape under tension.",
            output_html=f"braid_{name}.html",
        )
        print(
            f"braid_{name}.html  {n_strands} strands, "
            f"{len(braid.generators)} generators, period {paths[0].length}"
        )


def ropes() -> None:
    """The rope, whose radius contact decides and a search finds."""
    diameter = 0.4
    for name, n_strands, title in ROPES:
        lay = minimum_lay(n_strands, diameter) * 2.0
        radius = lay_radius(n_strands, diameter, lay)
        helices = rope_helices(
            n_strands, diameter=diameter, length=lay, turns=1.0, radius=radius
        )

        braid = ParametricBraid([_as_parametric(helix) for helix in helices])
        caption = (
            f"{title} \u2014 lay {lay:.2f}, radius {radius:.4f} found by "
            f"squeezing until the strands touch ({diameter} thick)"
        )
        braid.plot(n_sample=1200, title=caption, output_html=f"braid_{name}.html")
        braid.plot(
            n_sample=600,
            tube_diameter=diameter,
            title=f"{caption} \u2014 drawn as yarn, so the touching can be seen",
            output_html=f"braid_{name}_yarn.html",
        )
        print(
            f"braid_{name}.html  {n_strands} strands, lay {lay:.2f} "
            f"(shortest possible {minimum_lay(n_strands, diameter):.2f}), "
            f"radius {radius:.5f} vs {packing_radius(n_strands, diameter):.5f} "
            f"if they ran straight, clearance "
            f"{closest_approach(helices, 500):.5f} vs {diameter} thick"
        )


# (name, strands, braid angle in degrees, title)
TUBES = [
    (
        "tube_4",
        4,
        45,
        "Braided tube \u2013 4 strands at 45\u00b0, the narrowest there is",
    ),
    ("tube_8", 8, 45, "Braided tube \u2013 8 strands at 45\u00b0"),
    ("tube_16", 16, 45, "Braided tube \u2013 16 strands at 45\u00b0"),
    ("tube_8_steep", 8, 65, "Braided tube \u2013 8 strands at 65\u00b0"),
]


def sinnets() -> None:
    """The classical flat sinnet of five strands, ABOK 2967.

    Worth drawing beside the figure-eight family, because they are *not* the
    same braid.  The family reproduces the everyday three-strand plait
    exactly; at five strands it produces something else with the same number
    of crossings, which Dehornoy reduction says is a different element of the
    braid group.  ABOK moves the outer strands alternately, each travelling
    right across the braid; the family has every strand swinging at once.
    """
    import contextlib
    import io

    from braidpy.braid_catalog import flat_sinnet5

    with contextlib.redirect_stdout(io.StringIO()):
        braid, _ = flat_sinnet5()

    diameter = 0.4
    paths = strand_paths(braid, spacing=0.5, amplitude=0.25, profile=SMOOTHSTEP)
    strands = [path.to_parametric() for path in paths]
    clearance = closest_approach(paths, 500)

    caption = (
        "Flat sinnet \u2013 5 strands, ABOK 2967 "
        f"\u2014 {len(braid.generators)} crossings to the period, the outer "
        "strands moved alternately.  A drawing, not a shape under tension."
    )
    ParametricBraid(strands).plot(
        n_sample=1200, title=caption, output_html="braid_sinnet_5.html"
    )
    ParametricBraid(strands).plot(
        n_sample=600,
        tube_diameter=min(diameter, clearance),
        title=f"{caption} \u2014 drawn as yarn",
        output_html="braid_sinnet_5_yarn.html",
    )
    print(
        f"braid_sinnet_5.html  5 strands, word {list(braid.generators[:4])} "
        f"repeated {len(braid.generators) // 4}, period {paths[0].length}, "
        f"drawn clearance {clearance:.4f} "
        f"(yarn drawn at {min(diameter, clearance):.3f})"
    )


def tubes() -> None:
    """A braided tube, after the published geometric model.

    Strands wind round the tube at a fixed angle while their distance from
    the axis swings out and in — out over, in under.  The swing is the braid.
    """
    diameter = 0.4
    for name, n_strands, degrees, title in TUBES:
        angle = math.radians(degrees)
        radius = tubular_braid_radius(n_strands, diameter, angle)
        strands = tubular_braid(n_strands, radius, angle, diameter)
        clearance = tubular_braid_clearance(strands, 600)

        braid = ParametricBraid([_as_parametric(strand) for strand in strands])
        caption = (
            f"{title} \u2014 radius {radius:.3f} (narrowest that does not crowd), "
            f"strands {diameter} thick, once round in {strands[0].length:.2f}"
        )
        braid.plot(n_sample=1400, title=caption, output_html=f"braid_{name}.html")
        braid.plot(
            n_sample=700,
            tube_diameter=diameter,
            title=f"{caption} \u2014 drawn as yarn",
            output_html=f"braid_{name}_yarn.html",
        )
        print(
            f"braid_{name}.html  {n_strands} strands at {degrees}\u00b0, "
            f"radius {radius:.4f} "
            f"({'climb' if crossing_binds_above(n_strands, angle) else 'swing'}"
            f"-bound; seated at "
            f"{packing_radius(n_strands, diameter):.4f}), "
            f"clearance {clearance:.4f} vs {diameter} thick, "
            f"once round in {strands[0].length:.3f}, "
            f"covering {cover_factor(n_strands, radius, angle, diameter):.2f} "
            f"of the tube"
        )

    # The same braid drawn tight, which the round-strand model cannot
    # honestly reach: at a cover of 0.9 the strands are a third of a
    # diameter into one another.  Real yarn flattens where it crosses; this
    # is what that would look like.
    n_strands, degrees, cover = 8, 45, 0.9
    angle = math.radians(degrees)
    radius = radius_for_cover(n_strands, diameter, angle, cover)
    strands = tubular_braid(n_strands, radius, angle, diameter)
    overlap = diameter - tubular_braid_clearance(strands, 600)
    braid = ParametricBraid([_as_parametric(strand) for strand in strands])
    caption = (
        f"Braided tube \u2013 {n_strands} strands at {degrees}\u00b0, drawn tight "
        f"\u2014 covering {cover:.0%} of the tube, which round strands cannot "
        f"do: they overlap by {overlap:.2f} of a {diameter} diameter"
    )
    braid.plot(n_sample=1400, title=caption, output_html="braid_tube_tight.html")
    braid.plot(
        n_sample=700,
        tube_diameter=diameter,
        title=f"{caption} \u2014 drawn as yarn",
        output_html="braid_tube_tight_yarn.html",
    )
    print(
        f"braid_tube_tight.html  {n_strands} strands at {degrees}\u00b0, "
        f"radius {radius:.4f} for {cover:.0%} cover, "
        f"strands overlapping by {overlap:.4f} of {diameter} \u2014 "
        f"what flattened yarn would allow, not round"
    )


def plaits() -> None:
    """The classic flat braid, optimised within its closed-form family."""
    diameter = 0.4
    for name, n_strands, ratio, title in PLAITS:
        period = ratio * diameter
        found = tightest_figure_eight(diameter, period, n_strands=n_strands)
        if found is None:
            print(f"braid_{name}.html  no shape of the family fits P={period:.2f}")
            continue
        amplitude, height = found
        strands = figure_eight_strands(-amplitude, -height, period, n_strands)
        word = braid_word(strands, n_samples=60000)

        braid = ParametricBraid([_as_parametric(strand) for strand in strands])
        caption = (
            f"{title} \u2014 A={amplitude:.3f}, H={height:.3f}, "
            f"P={period:.2f}, strands {diameter} thick and touching, "
            f"{len(word)} crossings to the period"
        )
        braid.plot(n_sample=900, title=caption, output_html=f"braid_{name}.html")
        braid.plot(
            n_sample=500,
            tube_diameter=diameter,
            title=f"{caption} \u2014 drawn as yarn",
            output_html=f"braid_{name}_yarn.html",
        )
        print(
            f"braid_{name}.html  A={amplitude:.4f} H={height:.4f} "
            f"{n_strands} strands, "
            f"A/H={amplitude / height:.2f} P={period:.2f} ({ratio:g} d), "
            f"clearance {figure_eight_clearance(amplitude, height, period, n_strands, 300):.5f} "
            f"vs {diameter} thick, {len(word)} crossings "
            f"(n(n-1) = {n_strands * (n_strands - 1)})"
        )


def _as_parametric(helix):
    """A helix on t in [0, 1], for whatever wants a parametric strand."""
    from braidpy.parametric_strand import ParametricStrand

    return ParametricStrand(lambda t: helix.position(t * helix.length))


def main() -> None:
    drawn_braids()
    print()
    ropes()
    print()
    plaits()
    print()
    sinnets()
    print()
    tubes()
    print(
        f"\n{len(BRAIDS) + 2 * (len(ROPES) + len(PLAITS) + len(TUBES)) + 4}"
        " pages written."
    )


if __name__ == "__main__":
    main()
