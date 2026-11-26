# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""`machine_catalog` was renamed `braidpy.machine_catalogue`: one spelling for the catalogues.

Kept so the older imports go on working.  Anything this module answers,
`braidpy.machine_catalogue` answers, under its own name.
"""

import warnings

from braidpy import machine_catalogue

_warned = False


def __getattr__(name: str):
    global _warned
    if not _warned:
        _warned = True
        warnings.warn(
            "braidpy.machine_catalog is now braidpy.machine_catalogue; import it under its new name.",
            DeprecationWarning,
            stacklevel=2,
        )
    return getattr(machine_catalogue, name)
