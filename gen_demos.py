"""Generate the horn gear braiding machine demo pages.

Writes one static diagram, one track diagram, and an animation per machine,
then the braid each wired machine lays, in 3D: with no tension, and drawn in
to a braiding point and tightened — and the same for a braid word and a
mobidai, which are laid the same way.
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
from braidpy.take_off import (  # noqa: E402
    braid_word_trajectories,
    lay_yarns,
    mobidai_braid,
)
from braidpy.disk_animation import animate_kumihimo, animate_mobidai  # noqa: E402
from braidpy.mobidai_catalog import KONGO_8  # noqa: E402
from braidpy.take_off import visualize_yarns as visualize_yarns_from  # noqa: E402
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


def other_sources() -> int:
    """Braids laid from something other than a machine: a word and a disk."""
    # A three-strand plait, from nothing but its braid word.
    word = braid_word_trajectories([1, -2] * 6)
    plait, _ = tighten_yarns(
        lay_yarns(word, yarn_diameter=0.45, fell_radius=0.0), 0.45, iterations=150
    )
    visualize_yarns_from(
        plait,
        title="Three-strand plait, from its braid word — tightened",
        output_html="demo_word_plait_braid.html",
    )
    print("demo_word_plait_braid.html")

    # Kongo gumi on eight strands, from the catalogue: two strands at the
    # top, two at the bottom and two each side, as a disk is threaded.  Each
    # cycle leaves the pairs a slot back, and the next is made from there.
    kongo = KONGO_8.to_config()
    animate_mobidai(
        kongo,
        n_cycles=8,
        slot_offset=0.5,
        side_view=True,
        title="Kumihimo, kongo gumi on 8 strands — the disk, and the braid below",
        output_html="demo_kumihimo_8.html",
    )
    print("demo_kumihimo_8.html")
    # The braid itself: its crossings, laid round a ring and tightened.
    braid = mobidai_braid(kongo, 0.12, n_cycles=8)
    visualize_yarns_from(
        braid,
        title="Kumihimo, kongo gumi on 8 strands — tightened",
        colors=[colour for _, colour in KONGO_8.initial_slots],
        output_html="demo_kumihimo_8_braid.html",
    )
    print("demo_kumihimo_8_braid.html")

    # Kumihimo's own model: swap top and bottom, turn a quarter.
    animate_kumihimo(
        "SR" * 8, n_strands=8, side_view=True, output_html="demo_kumihimo_sr_8.html"
    )
    print("demo_kumihimo_sr_8.html")
    return 4


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

    yarn_pages += other_sources()

    print(f"\n{len(MACHINES) + 2 + yarn_pages} pages written.")


if __name__ == "__main__":
    main()
