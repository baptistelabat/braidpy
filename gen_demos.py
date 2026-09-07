"""Generate the horn gear braiding machine demo pages.

Writes one static diagram, one track diagram, and an animation per machine.
Run from the repository root: ``python gen_demos.py``
"""

import sys

sys.path.insert(0, "src")

from braidpy.horn_gear import (  # noqa: E402
    animate,
    compute_tracks,
    visualize_machine,
    visualize_tracks,
)
from braidpy.horn_gear.examples import (  # noqa: E402
    diamond_braid,
    flat_braid_3,
    flat_braid_4,
    flat_braid_9,
    tubular_braid_8,
    tubular_braid_12,
    tubular_braid_16,
)

MACHINES = [
    ("flat_3", flat_braid_3, 12, "Flat braid – 3 carriers (simplest machine)"),
    ("flat_4", flat_braid_4, 8, "Flat braid – 4 carriers"),
    ("flat_9", flat_braid_9, 24, "Flat braid – 9 carriers, single track"),
    ("tubular_8", tubular_braid_8, 16, "Tubular braid – 8 carriers"),
    ("tubular_12", tubular_braid_12, 16, "Tubular braid – 12 carriers"),
    ("tubular_16", tubular_braid_16, 16, "Tubular braid – 16 carriers"),
    ("diamond", diamond_braid, 16, "Diamond braid – 8 carriers"),
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
