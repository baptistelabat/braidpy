# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy alone, without its viz extra: it computes all it computes, and
asked to draw, it says what to install."""

import subprocess
import sys

# Run with the drawing libraries made unimportable, as if not installed.
WITHOUT_DRAWING = """
import sys
for name in ("matplotlib", "mpl_toolkits", "plotly", "imageio"):
    sys.modules[name] = None
"""


def _run(script):
    return subprocess.run(
        [sys.executable, "-c", WITHOUT_DRAWING + script],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_braidpy_computes_without_its_drawing_libraries():
    """Braids, their words and properties, the machines, the sinnets, the
    bridges and Braid Studio's braids need nothing that draws."""
    out = _run(
        """
from braidpy import Braid, tools, web
from braidpy.horn_gear.examples import tubular_braid_8
from braidpy.horn_gear.tracks import compute_tracks
from braidpy.solid_sinnets_catalog import abok_3042
b = Braid([1, 2, -1])
b.draw()
print(b.format_to_notation(target="alpha"))
print(tools.compare_braids("1 -2", "-2 1")["same_braid"])
print(len(compute_tracks(tubular_braid_8())))
print(abok_3042.braid().n_strands)
print(len(web.build({"source": "word", "word": "1 -2", "n_strands": 3}, tighten=False)["strands"]))
"""
    )
    assert out.split()[-5:] == ["abA", "True", "4", "8", "3"]


def test_drawing_without_the_viz_extra_says_what_to_install():
    out = _run(
        """
from braidpy import Braid
try:
    Braid([1, 2, -1]).plot()
except ModuleNotFoundError as missing:
    print(missing)
"""
    )
    assert "pip install 'braidpy[viz]'" in out
