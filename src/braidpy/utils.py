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

from __future__ import annotations

import importlib
from collections.abc import Sequence
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # typing.Self is 3.11's; braidpy does not depend on typing_extensions,
    # nor does a browser load it (Pyodide).
    from typing_extensions import Self

# Colours to tell strands apart, one after the other: the carriers of a
# braiding machine's animation, and the yarns drawn from them.
PALETTE = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
    "#f781bf",
    "#999999",
    "#66c2a5",
    "#fc8d62",
    "#8da0cb",
    "#e78ac3",
]

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
    """Colorize a string using a repeating color based on index (starting at 0).

    Args:
        text: The string to colorize.
        index: The index used to determine the color.

    Returns:
        str: The colorized string.
    """
    color = ANSI_COLORS[index % len(ANSI_COLORS)]
    return f"{color}{text}{RESET}"


def colorize(item: str | int, index: int | None = None) -> str:
    """Colorize item based on index (or its value if it's an int).

    Args:
        item: The item to colorize (string or integer).
        index: Optional index to use for color selection. If None, uses the
            item's value (if int) or 0.

    Returns:
        str: The colorized string representation of the item.
    """
    if index is None:
        index = item - 1 if isinstance(item, int) else 0
    return colorize_by_index(str(item), index)


def int_to_superscript(n: int) -> str:
    """Convert an integer to its superscript representation.

    Args:
        n: The integer to convert.

    Returns:
        str: The superscript representation of the integer.
    """
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
    """Convert an integer to its subscript representation.

    Args:
        n: The integer to convert.

    Returns:
        str: The subscript representation of the integer.
    """
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


if TYPE_CHECKING:
    # To a type checker these are the numbers they check: a literal default
    # such as ``n: StrictlyPositiveInt = 100`` is then fine.
    PositiveFloat = float
    StrictlyPositiveFloat = float
    PositiveInt = int
    StrictlyPositiveInt = int
else:

    class PositiveFloat(float):
        def __new__(cls, value: Any) -> Self:
            val = float(value)
            if val < 0:
                raise ValueError(f"Value must be >= 0, got {val}")
            return super().__new__(cls, val)

    class StrictlyPositiveFloat(float):
        def __new__(cls, value: Any) -> Self:
            val = float(value)
            if val <= 0:
                raise ValueError(f"Value must be > 0, got {val}")
            return super().__new__(cls, val)

    class PositiveInt(int):
        def __new__(cls, value: Any) -> Self:
            val = int(value)
            if val < 0:
                raise ValueError(f"Value must be >= 0, got {val}")
            return super().__new__(cls, val)

    class StrictlyPositiveInt(int):
        def __new__(cls, value: Any) -> Self:
            val = int(value)
            if val <= 0:
                raise ValueError(f"Value must be > 0, got {val}")
            return super().__new__(cls, val)


# What braidpy draws with, from its viz extra: not installed with braidpy
# alone.
_DRAWING = {"matplotlib", "mpl_toolkits", "plotly", "imageio"}


class _LazyModule(ModuleType):
    """A module imported the first time something is asked of it."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._lazy_name = name
        self._lazy_module: ModuleType | None = None

    def __getattr__(self, attr: str) -> Any:
        if attr.startswith("_lazy_"):
            raise AttributeError(attr)
        if self._lazy_module is None:
            try:
                self._lazy_module = importlib.import_module(self._lazy_name)
            except ModuleNotFoundError as missing:
                if (missing.name or "").split(".")[0] not in _DRAWING:
                    raise
                raise ModuleNotFoundError(
                    f"{missing.name} is needed to draw braids, and is not "
                    "installed: pip install 'braidpy[viz]'",
                    name=missing.name,
                ) from missing
        return getattr(self._lazy_module, attr)


def lazy_module(name: str) -> Any:
    """A module that is only imported when first used.

    Drawing libraries — plotly, matplotlib — are heavy, and most of braidpy
    computes without them: in a browser, through Pyodide, not loading them
    is the difference between a page that opens and one that downloads tens
    of megabytes first.  Modules that draw import them this way, and keep
    the real import under ``TYPE_CHECKING`` for the type checker.

    Args:
        name: The module's dotted name.

    Returns:
        A stand-in that imports the module on first attribute access.
    """
    return _LazyModule(name)


class FunctionalException(Exception):
    pass


def play_controls(
    frame_duration_ms: float, marks: Sequence[tuple[str, str]]
) -> dict[str, list[dict[str, Any]]]:
    """Play and pause buttons, and a slider, for a Plotly animation.

    Args:
        frame_duration_ms: How long each frame is shown while playing.
        marks: The slider's notches, as (frame name, label).

    Returns:
        ``updatemenus`` and ``sliders``, for ``Figure.update_layout``.  The
        slider's read-out is hidden: Plotly's repeats the active notch's
        label, and notches between two labelled ones have none to repeat,
        so it would blank out while the animation ran.
    """
    still = {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}
    return {
        "updatemenus": [
            dict(
                type="buttons",
                showactive=False,
                y=1.08,
                x=0.5,
                xanchor="center",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": frame_duration_ms,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                            },
                        ],
                    ),
                ],
            )
        ],
        "sliders": [
            dict(
                steps=[
                    dict(args=[[name], still], label=label, method="animate")
                    for name, label in marks
                ],
                active=0,
                x=0,
                y=0,
                xanchor="left",
                len=1.0,
                currentvalue=dict(visible=False),
                transition=dict(duration=0),
            )
        ],
    }
