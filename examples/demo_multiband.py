# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Animate the three-band 10-15-10 machine, loaded as its drawing is.

    python examples/demo_multiband.py

Writes ``demo_multiband_machine.html``, the machine, and
``demo_multiband_animated.html``, its carriers turning.  See
:mod:`braidpy.horn_gear.multiband` for the split gears that keep the three
bands apart.
"""

from braidpy.horn_gear.multiband import band_of, multiband_10_15_10
from braidpy.horn_gear.tracks import compute_tracks, simulation_period
from braidpy.horn_gear.visualization import animate, visualize_machine

#: Steps to animate, and frames drawn per step.
N_STEPS = 24
N_SUBSTEPS = 6


def main() -> None:
    machine = multiband_10_15_10()
    carriers = machine.default_carriers()
    per_band = [0, 0, 0]
    for gear, _ in carriers.values():
        per_band[band_of(gear)] += 1
    print(
        f"{len(machine.gears)} gears and halves, {machine.total_slots()} slots, "
        f"{len(compute_tracks(machine))} tracks, period {simulation_period(machine)}"
    )
    print(f"{len(carriers)} carriers: {' / '.join(map(str, per_band))}")
    visualize_machine(
        machine,
        output_html="demo_multiband_machine.html",
        title="3-band 10-15-10 line",
    )
    animate(
        machine,
        n_steps=N_STEPS,
        n_substeps=N_SUBSTEPS,
        carrier_positions=carriers,
        output_html="demo_multiband_animated.html",
        title=f"3-band 10-15-10 line - {len(carriers)} carriers",
    )
    print("wrote demo_multiband_machine.html and demo_multiband_animated.html")


if __name__ == "__main__":
    main()
