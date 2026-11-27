# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Old names kept working after a rename, each saying its new name.

braidpy spells its names in American English, as Python and its libraries
do (``color``, ``center``, ``neighbor``); a name once spelled otherwise goes
on answering, with a :class:`DeprecationWarning`, so code written against
it does not break.
"""

from __future__ import annotations

import functools
import warnings
from collections.abc import Callable, Mapping
from typing import Any, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# The warning points at the caller of the old name, past this module.
_CALLER = 3


def _warn(old: str, new: str) -> None:
    warnings.warn(
        f"{old} is now {new}; use it under its new name.",
        DeprecationWarning,
        stacklevel=_CALLER,
    )


def renamed_keywords(**old_to_new: str) -> Callable[[F], F]:
    """A function taking its old keyword arguments under their new names.

    Args:
        old_to_new: Each old keyword, as the new one it now is.

    Returns:
        The decorator.
    """

    def decorate(function: F) -> F:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for old, new in old_to_new.items():
                if old in kwargs:
                    _warn(f"{function.__qualname__}({old}=)", f"{new}=")
                    kwargs[new] = kwargs.pop(old)
            return function(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorate


class renamed_attribute:  # lower case: used where a property would be
    """An attribute under its old name, read and written as the new one.

    Held by the class under the old name: ``color = renamed_attribute("colour")``.

    Args:
        new: The attribute's new name.
    """

    def __init__(self, new: str) -> None:
        self.new = new
        self.old = new

    def __set_name__(self, owner: type, name: str) -> None:
        self.old = f"{owner.__name__}.{name}"

    def __get__(self, instance: Any, owner: Optional[type] = None) -> Any:
        if instance is None:
            return self
        _warn(self.old, f"{type(instance).__name__}.{self.new}")
        return getattr(instance, self.new)

    def __set__(self, instance: Any, value: Any) -> None:
        _warn(self.old, f"{type(instance).__name__}.{self.new}")
        setattr(instance, self.new, value)


def renamed_globals(module: str, old_to_new: Mapping[str, str]) -> Callable:
    """A module's ``__getattr__`` answering its old names as the new.

    Args:
        module: The module's name, ``__name__``.
        old_to_new: Each old name, as the new one it now is.

    Returns:
        The ``__getattr__``, for the module to hold.
    """
    import sys

    def __getattr__(name: str) -> Any:
        if name in old_to_new:
            new = old_to_new[name]
            _warn(f"{module}.{name}", f"{module}.{new}")
            return getattr(sys.modules[module], new)
        raise AttributeError(f"module {module!r} has no attribute {name!r}")

    return __getattr__
