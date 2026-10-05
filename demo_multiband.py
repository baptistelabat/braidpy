# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Animate the three-band 10-15-10 machine, with a loading you choose.

Run it from a checkout of this branch::

    cd ~/CascadeProjects/braidpy-multiband
    PYTHONPATH=$PWD/src ~/CascadeProjects/braidpy/.venv/bin/python demo_multiband.py

The ``PYTHONPATH`` matters: braidpy is installed into the virtualenv from the
main checkout, which is on another branch and has no switch module, so without
it the import fails with ``No module named 'braidpy.horn_gear.switch'``.

Edit :data:`LOADING` to put the carriers where you want them.  Set it to None
to have the script search for the fullest loading it can find instead.

A loading that cannot run is still drawn, up to the last step before it goes
wrong, so the trouble can be watched rather than only read about.  The step it
fails at and the carriers that meet are printed as well.
"""

import random
from typing import Dict, List, Optional, Tuple

from braidpy.horn_gear.layout import compute_layout
from braidpy.horn_gear.simulation import CollisionError, simulate
from braidpy.horn_gear.switch import (
    MULTIBAND_10_15_10_BANDS,
    MULTIBAND_10_15_10_CARRIERS,
    MULTIBAND_10_15_10_SLOTS,
    multiband_10_15_10,
)
from braidpy.horn_gear.tracks import compute_tracks
from braidpy.horn_gear.visualization import animate, visualize_machine

#: Where the carriers start, as (gear, slot).  The gears are G0 to G15 along
#: the line, with these slot counts::
#:
#:     G0  G1  G2  G3  G4  G5  G6  G7  G8  G9 G10 G11 G12 G13 G14 G15
#:      5   4   4   8   6   8   4   4   4   4   8   6   8   4   4   5
#: Each 6-slot gear is switched on *both* of its contacts -- G3-G4 and G4-G5
#: for the first, G10-G11 and G11-G12 for the second -- so carriers arriving
#: from either side ride round it and go back the way they came.
#:
#: Bands: G0-G4, G4-G11, G11-G15.  The two 6-slot gears belong to the bands on
#: both sides of them.  Set to None to search for the fullest loading instead.
LOADING: Optional[List[Tuple[str, int]]] = None

#: Steps of the machine to animate, and frames drawn per step.
N_STEPS = 12
N_SUBSTEPS = 3

#: How many steps a loading must survive before it is called good.
CHECK_STEPS = 150


def all_positions() -> List[Tuple[str, int]]:
    """Every (gear, slot) on the machine."""
    return [
        (f"G{i}", slot)
        for i, n in enumerate(MULTIBAND_10_15_10_SLOTS)
        for slot in range(n)
    ]


def runs(machine, places: List[Tuple[str, int]], steps: int = CHECK_STEPS) -> bool:
    """Whether these carriers can run without meeting."""
    try:
        simulate(machine, steps, dict(enumerate(places)))
    except CollisionError:
        return False
    return True


def search(machine, trials: int = 25) -> List[Tuple[str, int]]:
    """The fullest loading a greedy search finds.

    Args:
        machine: The machine to load.
        trials: Random orders to try; more trials, slightly fuller loadings.

    Returns:
        The carrier positions found.
    """
    best: List[Tuple[str, int]] = []
    for seed in range(trials):
        rng = random.Random(seed)
        order = all_positions()
        rng.shuffle(order)
        placed: List[Tuple[str, int]] = []
        for place in order:
            if runs(machine, placed + [place]):
                placed.append(place)
        if len(placed) > len(best):
            best = placed
    return best


def band_of(gear: str) -> Optional[int]:
    """Which band a gear belongs to; the first, for the two shared ones."""
    index = int(gear[1:])
    for band, (first, last) in enumerate(MULTIBAND_10_15_10_BANDS):
        if first <= index <= last:
            return band
    return None


def report(machine, places: List[Tuple[str, int]]) -> int:
    """Say what the loading is, and how far it gets.

    Args:
        machine: The machine to run.
        places: Where the carriers start.

    Returns:
        How many steps can be animated -- all of them if the loading runs, or
        the steps before it goes wrong if it does not.
    """
    per_band: Dict[int, int] = {0: 0, 1: 0, 2: 0}
    for gear, _ in places:
        per_band[band_of(gear)] += 1
    print(f"{len(places)} carriers: {per_band[0]} / {per_band[1]} / {per_band[2]}")
    print(f"the reference runs {' / '.join(map(str, MULTIBAND_10_15_10_CARRIERS))}")
    try:
        simulate(machine, CHECK_STEPS, dict(enumerate(places)))
    except CollisionError as exc:
        print(f"COLLIDES: {exc}")
        safe = max(0, exc.step - 1)
        print(f"animating the {safe} step(s) before it, so it can be watched")
        return safe
    print(f"runs {CHECK_STEPS} steps without a collision")
    return N_STEPS


def main() -> None:
    machine = multiband_10_15_10()
    tracks = compute_tracks(machine)
    print(
        f"{len(machine.gears)} gears, {machine.total_slots()} slots, "
        f"{len(tracks)} circuits -- two per band, one each way"
    )

    places = LOADING if LOADING is not None else search(machine)
    steps = report(machine, places)
    if steps == 0:
        print("the very first step collides; nothing to animate")
        return

    carriers = dict(enumerate(places))
    compute_layout(machine)  # fails loudly here rather than inside the drawing
    visualize_machine(
        machine,
        output_html="demo_multiband_machine.html",
        title="3-band 10-15-10 line",
    )
    animate(
        machine,
        n_steps=steps,
        n_substeps=N_SUBSTEPS,
        carrier_positions=carriers,
        output_html="demo_multiband_animated.html",
        title=f"3-band 10-15-10 line - {len(places)} carriers",
    )
    print("wrote demo_multiband_machine.html and demo_multiband_animated.html")


if __name__ == "__main__":
    main()
