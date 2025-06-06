# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: utils.py
Description: Utility functions, not directly related to braids
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from typing import Optional, Union, Any

# ANSI color codes (foreground)
ANSI_COLORS = [
    "\033[31m",  # Red
    "\033[32m",  # Green
    "\033[34m",  # Blue
    "\033[33m",  # Yellow
    "\033[35m",  # Magenta
    "\033[36m",  # Cyan
]
RESET = "\033[0m"

terminal_colors = {
    0: "red",  # Red
    1: "green",  # Green
    2: "blue",  # Blue
    3: "yellow",  # Yellow
    4: "magenta",  # Magenta
    5: "cyan",  # Cyan
    6: "orange",  # Orange
    7: "purple",  # Purple
    8: "brown",  # Brown
    9: "rgb(0,128,128)",  # Teal
}


def colorize_by_index(text: str, index: int) -> str:
    """Colorize a string using a repeating color based on index (starting at 0)."""
    color = ANSI_COLORS[index % len(ANSI_COLORS)]
    return f"{color}{text}{RESET}"


def colorize(item: Union[str, int], index: Optional[int] = None) -> str:
    """Colorize item based on index (or its value if it's an int)."""
    if index is None:
        index = item - 1 if isinstance(item, int) else 0
    return colorize_by_index(str(item), index)


def int_to_superscript(n: int) -> str:
    superscript_map = {
        "-": "\u207b",  # superscript minus
        "0": "\u2070",
        "1": "\u00b9",
        "2": "\u00b2",
        "3": "\u00b3",
        "4": "\u2074",
        "5": "\u2075",
        "6": "\u2076",
        "7": "\u2077",
        "8": "\u2078",
        "9": "\u2079",
    }
    return "".join(superscript_map[ch] for ch in str(n))


def int_to_subscript(n: int) -> str:
    subscript_map = {
        "-": "\u208b",  # subscript minus
        "0": "\u2080",
        "1": "\u2081",
        "2": "\u2082",
        "3": "\u2083",
        "4": "\u2084",
        "5": "\u2085",
        "6": "\u2086",
        "7": "\u2087",
        "8": "\u2088",
        "9": "\u2089",
    }
    return "".join(subscript_map[ch] for ch in str(n))


class PositiveFloat(float):
    def __new__(cls: "PositiveFloat", value: Any) -> "PositiveFloat":
        val = float(value)
        if val < 0:
            raise ValueError(f"Value must be >= 0, got {val}")
        return super().__new__(cls, val)


class StrictlyPositiveFloat(float):
    def __new__(cls: "StrictlyPositiveFloat", value: Any) -> "StrictlyPositiveFloat":
        val = float(value)
        if val <= 0:
            raise ValueError(f"Value must be > 0, got {val}")
        return super().__new__(cls, val)


class PositiveInt(int):
    def __new__(cls: "PositiveInt", value: Any) -> "PositiveInt":
        val = int(value)
        if val < 0:
            raise ValueError(f"Value must be >= 0, got {val}")
        return super().__new__(cls, val)


class StrictlyPositiveInt(int):
    def __new__(cls: "StrictlyPositiveInt", value: Any) -> "StrictlyPositiveInt":
        val = int(value)
        if val <= 0:
            raise ValueError(f"Value must be > 0, got {val}")
        return super().__new__(cls, val)


class FunctionalException(Exception):
    pass
