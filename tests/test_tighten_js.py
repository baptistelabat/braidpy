# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/tighten.js, the page's sideways tightening, against braidpy's own."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from braidpy.web import build


def _node_tighten(job):
    out = subprocess.run(
        [
            "node",
            "-e",
            (
                "const {tightenYarns} = require(process.argv[1]);"
                "const job = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
                "const r = tightenYarns(job);"
                "console.log(JSON.stringify({xy: Array.from(r.xy), closest: r.closest}));"
            ),
            str(Path(__file__).resolve().parent.parent / "web" / "tighten.js"),
        ],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
@pytest.mark.parametrize(
    "spec",
    [
        {"source": "word", "word": "1 -2", "repeat": 4},
        {"source": "kumihimo", "pattern": "SR", "n_strands": 8, "repeat": 2},
        {"source": "machine", "name": "tubular_8", "cycles": 1},
        # Round cores held straight.  Every yarn meets at the braiding
        # point, beside them, and which way two part there is decided by
        # the last digit: alike in the end, not step for step.
        {
            "source": "machine",
            "name": "soutache_7",
            "cycles": 1,
            "cores": "rigid",
            "ties": True,
        },
        # Kept outside a core round the axis, as tighten_yarns can.
        {
            "source": "kumihimo",
            "pattern": "SR",
            "n_strands": 8,
            "repeat": 2,
            "core_radius": 0.06,
        },
    ],
)
@pytest.mark.slow
def test_the_page_tightens_as_braidpy_does(spec):
    """web/tighten.js is tighten_yarns, step for step.

    Exactly so at first.  Over many steps, rounding differs enough for the
    contact pushes, which switch on and off at a threshold, to take the two
    apart a little — into braids that are as tight and as clear as each
    other.
    """
    import numpy as np

    from braidpy.take_off import tighten_yarns

    core = spec.pop("core_radius", None) if "core_radius" in spec else None
    ties = spec.pop("ties", False)
    handed = build({**spec, "iterations": 20}, tighten=False)
    job = {**handed["tighten"], "core_radius": core}
    n_yarns, n = job["n_yarns"], job["n"]

    # The laid yarns braidpy would have tightened, to the last digit: the
    # pushes would make even a rounding of them a different braid.
    laid = _laid_paths(spec)
    exact = laid.formed()[:, :, :2].reshape(-1).tolist()
    assert np.allclose(exact, job["xy"], atol=1e-8)
    # Exactly alike at first; tightened through, as tight and as clear.
    checks = [(300, None)] if ties else [(20, 1e-8), (300, None)]
    for iterations, close in checks:
        mine = _node_tighten({**job, "xy": exact, "iterations": iterations})
        theirs, history = tighten_yarns(
            laid,
            job["yarn_diameter"],
            iterations=iterations,
            core_radius=job["core_radius"],
            rigid=[k for k, stiff in zip(laid.points, job["rigid"]) if stiff],
        )
        xy_py = theirs.formed()[:, :, :2].reshape(-1)
        xy_js = np.array(mine["xy"])
        if close is not None:
            assert np.max(np.abs(xy_js - xy_py)) < close
        else:
            d = job["yarn_diameter"]
            assert mine["closest"] >= d * (1 - 3e-3)
            assert abs(mine["closest"] - history["closest"][-1]) < 0.01 * d

            # Length, the very thing tightening shortens: in 3D, every
            # sample at its height.  Sideways alone, a plait barely
            # shortens, and two equally tight ones can differ by more.
            heights = laid.formed()[:, :, 2:]

            def length(xy, heights=heights):
                yarns = np.concatenate([xy.reshape(n_yarns, n, 2), heights], axis=2)
                return np.sum(np.linalg.norm(np.diff(yarns, axis=1), axis=-1))

            assert abs(length(xy_js) / length(xy_py) - 1) < 0.02


def _laid_paths(spec):
    """The laid yarns ``build`` tightens, captured on their way."""
    from unittest import mock

    from braidpy import take_off

    captured = {}
    real = take_off.tighten_yarns

    def capture(paths, *args, **kwargs):
        captured.setdefault("paths", paths)
        return real(paths, *args, **{**kwargs, "iterations": 0})

    with mock.patch.object(take_off, "tighten_yarns", capture):
        build({**spec, "iterations": 20})
    return captured["paths"]
