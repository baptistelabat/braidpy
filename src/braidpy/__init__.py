# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy: braids in Python — represented, worked with and analysed,
and drawn and made, by hand or on a machine.
"""

from importlib.metadata import PackageNotFoundError as _NotInstalled
from importlib.metadata import version as _version

from .braid import Braid as Braid
from .properties import (
    alexander_polynomial as alexander_polynomial,
)
from .properties import (
    conjugacy_class as conjugacy_class,
)

try:
    __version__ = _version("braidpy")
except _NotInstalled:  # run from its sources, not installed (as in Pyodide)
    __version__ = "unknown"
