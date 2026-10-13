# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What every catalogue of braids in braidpy has in common.

Each catalogue — :mod:`braidpy.braid_catalog` (braid words),
:mod:`braidpy.mobidai_catalog` (kumihimo disk braids),
:mod:`braidpy.solid_sinnets_catalog` (Ashley's solid sinnets) and
:mod:`braidpy.horn_gear.examples` (braiding machines) — keeps its braids as
it likes best, and lists them in a ``CATALOGUE``: an :class:`Entry` per
braid, by the name it is known by, in the order to offer them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

__all__ = ["Entry"]

T = TypeVar("T")


@dataclass(frozen=True)
class Entry(Generic[T]):
    """One braid of a catalogue.

    Args:
        title: What it is called, to show.
        make: Makes it, as its catalogue keeps it: a braid, a disk braid's
            moves, a sinnet, a machine.  Nothing is drawn.
        reference: Where it comes from: a book and its number, a page.
    """

    title: str
    make: Callable[[], T]
    reference: str = ""
