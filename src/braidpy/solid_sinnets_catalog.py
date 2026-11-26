# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""`solid_sinnets_catalog` was renamed `braidpy.solid_sinnets_catalogue`: one spelling for the catalogues.

Kept so the older imports go on working.  Anything this module answers,
`braidpy.solid_sinnets_catalogue` answers, under its own name.
"""

import warnings

from braidpy import solid_sinnets_catalogue

_warned = False


def __getattr__(name: str):
    global _warned
    if not _warned:
        _warned = True
        warnings.warn(
            "braidpy.solid_sinnets_catalog is now braidpy.solid_sinnets_catalogue; import it under its new name.",
            DeprecationWarning,
            stacklevel=2,
        )
    return getattr(solid_sinnets_catalogue, name)
