# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/carried.js against braidpy.carried, the reference.

- The same algorithm: given the same numbers from the maths library
  (``tests/js_maths.py``), both make the very same braid, bead for bead.
- The same braid: each with its own maths library, which differ in the last
  place, the braid made crosses alike.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from js_maths import rounded_math

from braidpy.machine_catalog import CATALOGUE

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "carried_cases.js"

# Settlings a step, as braidpy.carried makes them; and steps of the plait
# for its first crossings to be taken off.
SUBSTEPS = 60
STEPS = 12


def _job(steps, substeps):
    from braidpy.carried import carriers_job

    return carriers_job(CATALOGUE["flat_3"].make(), steps, substeps=substeps)


def _js(case, tmp_path, job):
    path = tmp_path / "job.json"
    path.write_text(json.dumps(job))
    out = subprocess.run(
        ["node", str(CASES), case, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.slow
def test_the_page_makes_it_as_braidpy_does_bead_for_bead(tmp_path, monkeypatch):
    """A whole step of the flat plait: the same beads to the last digit,
    the same made, the same deepest press."""
    from braidpy import carried, form, rope

    for module in (rope, form, carried):
        monkeypatch.setattr(module, "math", rounded_math())
    job = _job(1, SUBSTEPS)
    js = _js("rounded", tmp_path, job)
    py = carried.make(job)
    assert py["made"] == js["made"]
    assert py["deepest"] == js["deepest"]
    assert py["yarns"] == js["yarns"]


@pytest.mark.slow
def test_the_page_makes_the_plait_the_machine_lays(tmp_path):
    """With its own maths, the page's plait, read above the ring, crosses as
    the braid laid off the machine does, crossing for crossing."""
    import numpy as np
    from test_carried import _crossings

    from braidpy.carried import RADIUS
    from braidpy.horn_gear import yarn_paths

    job = _job(STEPS, SUBSTEPS)
    js = _js("plain", tmp_path, job)
    height = job["ring"]["height"] + 2 * RADIUS
    yarns = [np.asarray(y).reshape(-1, 3) for y in js["yarns"]]
    made = _crossings([y[y[:, 2] > height] for y in yarns])
    laid = _crossings(
        [
            np.asarray(p)
            for p in yarn_paths(
                CATALOGUE["flat_3"].make(), n_steps=STEPS
            ).points.values()
        ]
    )
    assert len(made) >= STEPS // 2
    assert made == laid[: len(made)]
