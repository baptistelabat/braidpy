# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Reading what a page asks for: braid words, moves, numbers."""

from __future__ import annotations

import re
from typing import Any, List, Mapping, Sequence, Tuple

from braidpy.braidword import parse_word

__all__ = ["parse_moves", "parse_word"]


def parse_moves(text: str) -> List[Tuple[int, int]]:
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


def _numbers(text: Any, what: str) -> List[int]:
    numbers = [int(n) for n in re.findall(r"-?\d+", str(text))]
    if not numbers:
        raise ValueError(f"Give the {what}, as numbers.")
    return numbers


def _moves_text(moves: Sequence[Tuple[int, int]]) -> str:
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
