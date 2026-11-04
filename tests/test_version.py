# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy.__version__: the version installed, as pyproject.toml gives it."""

import re
from pathlib import Path

import braidpy


def test_the_version_is_the_one_released():
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    # Read by hand: tomllib is not in Python 3.10.
    released = re.search(
        r'^version = "([^"]+)"', pyproject.read_text(), re.MULTILINE
    ).group(1)
    assert braidpy.__version__ == released
