# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""`braidpy.catalogue` was renamed `braidpy.catalog`: one spelling for the catalogues.

Kept so the older imports go on working.  Anything this module answers,
`braidpy.catalog` answers, under its own name.
"""

import warnings

from braidpy import catalog

_warned = False


def __getattr__(name: str):
    global _warned
    if not _warned:
        _warned = True
        warnings.warn(
            "braidpy.catalogue is now braidpy.catalog; import it under its new name.",
            DeprecationWarning,
            stacklevel=2,
        )
    return getattr(catalog, name)
