# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Reading what a page asks for: braid words, moves, numbers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from braidpy.braidword import parse_word

__all__ = ["parse_moves", "parse_word"]


def parse_moves(text: str) -> list[tuple[int, int]]:
    """Moves from one place to another, as ``(from, to)`` pairs.

    Reads ``1>15, 17>31``, ``1->15; 17->31``, ``1 15, 17 31``, ``(1, 15)
    (17, 31)``, one move per line, and the like: what matters is the order
    of the numbers, taken two by two.

    Args:
        text: The moves.

    Returns:
        The moves, in order.

    Raises:
        ValueError: If there are no moves, or an odd number of places.
    """
    if re.search(r"[^\d\s,;:()\[\]>→\-]", text):
        raise ValueError("Write moves as from>to pairs, for example 1>15, 17>31.")
    numbers = [int(n) for n in re.findall(r"\d+", text)]
    if not numbers:
        raise ValueError("Give at least one move, for example 1>15.")
    if len(numbers) % 2:
        raise ValueError("Each move needs a place to go from and one to go to.")
    return list(zip(numbers[::2], numbers[1::2]))


def _numbers(text: Any, what: str) -> list[int]:
    numbers = [int(n) for n in re.findall(r"-?\d+", str(text))]
    if not numbers:
        raise ValueError(f"Give the {what}, as numbers.")
    return numbers


def _moves_text(moves: Sequence[tuple[int, int]]) -> str:
    return ", ".join(f"{a}>{b}" for a, b in moves)


def _number(spec: Mapping[str, Any], key: str, default: float, low: float, high: float):
    value = spec.get(key, default)
    if value is None or value == "":
        return default
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} should be a number, not {value!r}.") from None
    if not low <= value <= high:
        raise ValueError(f"{key} should be between {low:g} and {high:g}.")
    return value


def _count(spec: Mapping[str, Any], key: str, default: int, low: int, high: int) -> int:
    value = _number(spec, key, default, low, high)
    if value != int(value):
        raise ValueError(f"{key} should be a whole number.")
    return int(value)


@dataclass(frozen=True)
class Count:
    """A whole number a description may give as ``key``: its default, and the
    bounds it must keep to."""

    key: str
    default: int
    low: int
    high: int

    def read(self, spec: Mapping[str, Any], default: int | None = None) -> int:
        """The number given, checked; ``default`` if not, or this one's own."""
        own = self.default if default is None else default
        return _count(spec, self.key, own, self.low, self.high)


@dataclass(frozen=True)
class Number:
    """A number a description may give as ``key``: its default, and the
    bounds it must keep to."""

    key: str
    default: float
    low: float
    high: float

    def read(self, spec: Mapping[str, Any], default: float | None = None) -> float:
        """The number given, checked; ``default`` if not, or this one's own."""
        own = self.default if default is None else default
        return float(_number(spec, self.key, own, self.low, self.high))


_COLOUR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class Colours:
    """Colours a description may give as ``key``, one per strand.

    Given as a list, or as one string of them separated by commas, which is
    what fits in a link.  A strand the list does not reach keeps the colour
    whatever made the braid chose for it, so a description need only name the
    ones that were changed -- and an empty place leaves that strand alone:
    ``#e41a1c,,#4daf4a`` recolours the first and the third.
    """

    key: str

    def read(self, spec: Mapping[str, Any]) -> tuple[str | None, ...]:
        """The colours given, checked; empty if none.

        Args:
            spec: The description.

        Returns:
            One colour per strand named, None where a place was left empty.

        Raises:
            ValueError: If a colour is not ``#rgb`` or ``#rrggbb``.
        """
        given = spec.get(self.key)
        if given is None or given == "":
            return ()
        parts = (
            list(given) if isinstance(given, (list, tuple)) else str(given).split(",")
        )
        chosen: list[str | None] = []
        for part in parts:
            text = "" if part is None else str(part).strip()
            if not text:
                chosen.append(None)
                continue
            if not _COLOUR.match(text):
                raise ValueError(
                    f"{text!r} is not a colour: write it as #rgb or #rrggbb."
                )
            chosen.append(text.lower())
        return tuple(chosen)


@dataclass(frozen=True)
class Text:
    """Text a description may give as ``key``, and its default."""

    key: str
    default: str

    def read(self, spec: Mapping[str, Any]) -> str:
        """The text given, or the default."""
        return str(spec.get(self.key, self.default))


def defaults(
    *settings: Count | Number | Text,
) -> dict[str, str | int | float]:
    """The settings' defaults, by key: as the catalogue gives them."""
    return {setting.key: setting.default for setting in settings}
