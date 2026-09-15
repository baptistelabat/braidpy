"""Generate the horn gear braiding machine demo pages.

Writes one static diagram, one track diagram, and an animation per machine.
Run from the repository root: ``python gen_demos.py``
"""

import sys

sys.path.insert(0, "src")

from braidpy.horn_gear import (  # noqa: E402
    BraidingMachine,
    animate,
    compute_tracks,
    jacquard_lace_ring,  # noqa: E402
    tube_axials,
    visualize_machine,
    visualize_tracks,
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


MACHINES = [
    ("flat_3", flat_braid_3, 12, "Flat braid – 3 carriers (simplest machine)"),
    ("flat_4", flat_braid_4, 8, "Flat braid – 4 carriers"),
    ("flat_9", flat_braid_9, 24, "Flat braid – 9 carriers, single track"),
    ("soutache_5", soutache_braid, 20, "Soutache – 2 gears of 5, 5 carriers"),
    (
        "soutache_7",
        lambda: soutache_braid(n_slots=7),
        28,
        "Soutache – 2 gears of 7, 7 carriers",
    ),
    (
        "soutache_9",
        lambda: soutache_braid(n_slots=9),
        36,
        "Soutache – 2 gears of 9, 9 carriers",
    ),
    ("princess", princess_braid, 24, "Princess – 5/6/5 gears, 8 carriers over a cord"),
    ("tubular_8", tubular_braid_8, 16, "Tubular braid – 8 carriers"),
    (
        "tubular_8_cored",
        cored(tubular_braid_8),
        16,
        "Tubular braid – 8 carriers over a central core",
    ),
    ("tubular_12", tubular_braid_12, 16, "Tubular braid – 12 carriers"),
    ("tubular_16", tubular_braid_16, 16, "Tubular braid – 16 carriers"),
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
        animate(factory(), n_steps=n_steps, title=title, output_html=path)
        print(path)

    print(f"\n{len(MACHINES) + 2} pages written.")


if __name__ == "__main__":
    main()
