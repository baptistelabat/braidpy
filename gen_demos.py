"""Generate the horn gear braiding machine demo pages.

Writes one static diagram, one track diagram, and an animation per machine,
then the braid each wired machine lays, in 3D: with no tension, and drawn in
to a braiding point and tightened.
Run from the repository root: ``python gen_demos.py``
"""

import sys

sys.path.insert(0, "src")

from braidpy.horn_gear import (  # noqa: E402
    BraidingMachine,
    animate,
    compute_tracks,
    gear_radii,
    jacquard_lace_ring,  # noqa: E402
    tube_axials,
    visualize_machine,
    visualize_tracks,
    tighten_yarns,
    visualize_yarns,
    yarn_paths,
)
from braidpy.horn_gear.examples import (  # noqa: E402
    flat_braid_3,
    flat_braid_4,
    flat_braid_9,
    princess_braid,
    soutache_braid,
    tubular_braid_8,
    tubular_braid_12,
    tubular_braid_16,
)


def lace_program(n_gears, steps=8, hold=6):
    """A programme that walks a held block of gears round the ring.

    Everything is enabled except a run of `hold` gears, and that run moves on
    one place each step — so the held patch travels round the machine and
    leaves a diagonal in the lace.
    """
    program = []
    for step in range(steps):
        rows = []
        for parity in (0, 1):
            rows.append(
                "".join(
                    "1" if i % 2 == parity and not (step <= i < step + hold) else "0"
                    for i in range(n_gears)
                )
            )
        program.append((rows[0], rows[1]))
    return program


def cored(factory):
    """Same machine, with a core down each tube it braids."""

    def build():
        m = factory()
        return BraidingMachine(list(m.gears.values()), m.connections, tube_axials(m))

    return build


# (name, factory, n_steps, title).  ``None`` steps means one full cycle of the
# machine, which is what most of these want: the animation then ends where it
# began and the page loops without a jump.  A lace machine is given a length,
# because a programme need not bring its carriers back at all.
MACHINES = [
    ("flat_3", flat_braid_3, None, "Flat braid – 3 carriers (simplest machine)"),
    ("flat_4", flat_braid_4, None, "Flat braid – 4 carriers"),
    ("flat_9", flat_braid_9, None, "Flat braid – 9 carriers, single track"),
    ("soutache_5", soutache_braid, None, "Soutache – 2 gears of 5, 5 carriers"),
    (
        "soutache_7",
        lambda: soutache_braid(n_slots=7),
        None,
        "Soutache – 2 gears of 7, 7 carriers",
    ),
    (
        "soutache_9",
        lambda: soutache_braid(n_slots=9),
        None,
        "Soutache – 2 gears of 9, 9 carriers",
    ),
    (
        "princess",
        princess_braid,
        None,
        "Princess – 5/6/5 gears, 8 carriers over a cord",
    ),
    ("tubular_8", tubular_braid_8, None, "Tubular braid – 8 carriers"),
    (
        "tubular_8_cored",
        cored(tubular_braid_8),
        None,
        "Tubular braid – 8 carriers over a central core",
    ),
    ("tubular_12", tubular_braid_12, None, "Tubular braid – 12 carriers"),
    ("tubular_16", tubular_braid_16, None, "Tubular braid – 16 carriers"),
    (
        "jacquard_lace",
        lambda: jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")]),
        16,
        "Jacquard lace – 6 two-slot gears, C and D held every other step",
    ),
    (
        "jacquard_lace_48",
        lambda: jacquard_lace_ring(48, lace_program(48)),
        6,
        "Jacquard lace – 48 gears, a held block walking round the ring",
    ),
]


def main() -> None:
    reference = tubular_braid_8()
    visualize_machine(reference, output_html="demo_machine.html")
    visualize_tracks(
        reference, compute_tracks(reference), output_html="demo_tracks.html"
    )
    print("demo_machine.html, demo_tracks.html")

    for name, factory, n_steps, title in MACHINES:
        path = f"demo_{name}.html"
        fig = animate(factory(), n_steps=n_steps, title=title, output_html=path)
        print(f"{path} ({len(fig.frames)} frames)")

    # The braid each machine lays.  A lace machine is left out: its yarns go
    # wherever its programme sends them, and there is no repeat to show.
    yarn_pages = 0
    for name, factory, n_steps, title in MACHINES:
        if name.startswith("jacquard"):
            continue
        machine = factory()
        # A fifth of a gear radius is a plausible yarn.
        radii = gear_radii(machine)
        diameter = 0.2 * sum(radii.values()) / len(radii)
        path = f"demo_{name}_yarns.html"
        visualize_yarns(
            machine,
            title=f"{title} — yarns",
            tube_diameter=diameter,
            output_html=path,
        )
        print(path)

        # The same braid made at a braiding point, then pulled taut: it opens
        # out above the point into the shape its yarns settle to.
        braid, _ = tighten_yarns(
            yarn_paths(machine, yarn_diameter=diameter, fell_radius=0.0),
            diameter,
            iterations=150,
        )
        path = f"demo_{name}_braid.html"
        visualize_yarns(
            machine,
            braid,
            title=f"{title} — tightened braid, from a braiding point",
            output_html=path,
        )
        print(path)
        yarn_pages += 2

    print(f"\n{len(MACHINES) + 2 + yarn_pages} pages written.")


if __name__ == "__main__":
    main()
