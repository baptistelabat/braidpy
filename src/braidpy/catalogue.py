# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What every catalogue of braids in braidpy has in common.

Each catalogue — :mod:`braidpy.braid_catalog` (braid words),
:mod:`braidpy.mobidai_catalog` (kumihimo disk braids),
:mod:`braidpy.solid_sinnets_catalog` (Ashley's solid sinnets) and
:mod:`braidpy.machine_catalog` (braiding machines) — keeps its braids as
it likes best, and lists them in a ``CATALOGUE``: an :class:`Entry` per
braid, by the name it is known by, in the order to offer them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

__all__ = ["KINDS", "Entry", "Link", "ashley"]

T = TypeVar("T")

# What a link can be: where a braid is described, shown or made.
KINDS = ("book", "article", "video", "page", "post")


@dataclass(frozen=True)
class Link:
    """Where a braid comes from, or is shown being made.

    Args:
        title: What it is, to show: a book and its number, a video's title.
        kind: One of :data:`KINDS`.
        url: Where it is on the web; none for a book on paper, or a post
            known only by where it was.
    """

    title: str
    kind: str = "book"
    url: str = ""

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}, got {self.kind!r}")


def ashley(number: int | str) -> Link:
    """The Ashley Book of Knots, at a knot's number."""
    return Link(f"The Ashley Book of Knots, #{number}")


@dataclass(frozen=True)
class Entry(Generic[T]):
    """One braid of a catalogue.

    Args:
        title: What it is called, to show.
        make: Makes it, as its catalogue keeps it: a braid, a disk braid's
            moves, a sinnet, a machine.  Nothing is drawn.
        links: Where it comes from, and where it is shown: a book and its
            number, a video, a page.
    """

    title: str
    make: Callable[[], T]
    links: tuple[Link, ...] = ()

    @property
    def reference(self) -> str:
        """Where it comes from, as one line: the first link's title."""
        return self.links[0].title if self.links else ""
