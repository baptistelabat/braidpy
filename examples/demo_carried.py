# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A plait made by its carriers on the three-gear flat machine.

    python examples/demo_carried.py

Writes ``demo_carried_braid.html``, the braid formed above the forming
ring, its yarns as thick as they are, and ``demo_carried_machine.html``,
everything to scale: the deck, the carriers, the yarns' runs up to the ring
and the braid, as small as it is beside them.  See :mod:`braidpy.carried`.
"""

import time

from braidpy.carried import braid_by_carriers, figure
from braidpy.machine_catalog import CATALOGUE

#: The machine, and its steps to make.
MACHINE = "flat_3"
N_STEPS = 12


def main() -> None:
    started = time.time()
    braid = braid_by_carriers(
        CATALOGUE[MACHINE].make(),
        N_STEPS,
        progress=lambda p: print(
            f"step {p['step']} of {p['of']}, {time.time() - started:.0f} s"
        ),
    )
    for view in ("braid", "machine"):
        name = f"demo_carried_{view}.html"
        figure(braid, view).write_html(name)
        print(f"Wrote {name}")


if __name__ == "__main__":
    main()
