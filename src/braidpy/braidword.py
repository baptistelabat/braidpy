# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: braidword.py
Description: Functions for parsing and converting braid words
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

import re
from typing import List


def braidword_alpha_to_numeric(braidword: str) -> List[int]:
    """Convert an alphabetical braid word to its numerical representation.

    Each lowercase letter represents a braid generator σ_i, where:
        - 'a' → σ₁ → 1
        - 'b' → σ₂ → 2
        - ...

    Each uppercase letter represents the inverse generator σ_i⁻¹:
        - 'A' → σ₁⁻¹ → -1
        - 'B' → σ₂⁻¹ → -2
        - ...

    Special character # can be used for neutral element.

    Args:
        braidword: A string of alphabetical characters representing the braid
            word. Must contain only letters a-z and A-Z or character #.

    Returns:
        List[int]: The numerical representation of the braid word.

    Raises:
        ValueError: If the input contains non-alphabetical characters.

    Example:
        >>> braidword_alpha_to_numeric("abAB")
        [1, 2, -1, -2]
    """
    numeric_word: List[int] = []
    for ch in braidword:
        if ch == "#":
            num = 0
        elif ch.islower():
            num = ord(ch) - ord("a") + 1
        elif ch.isupper():
            num = -(ord(ch) - ord("A") + 1)
        else:
            raise ValueError(f"Invalid character in braidword: {ch}")
        numeric_word.append(num)
    return numeric_word


def parse_word(text: str) -> List[int]:
    """A braid word, as signed generator indices.

    Reads ``1 -2 1`` (or with commas), ``s1 s2^-1 s1`` (``σ`` too), and
    letters, ``aBa``: ``a`` is σ₁, ``b`` σ₂ and so on, a capital the inverse
    (:func:`braidword_alpha_to_numeric`).

    Args:
        text: The word.

    Returns:
        The generators; empty for an empty word.

    Raises:
        ValueError: If the text is none of these.
    """
    text = text.strip()
    if not text:
        return []
    if re.fullmatch(r"[A-Za-z]+", text) and not re.search(r"[sσ]\d", text):
        return braidword_alpha_to_numeric(text)
    word: List[int] = []
    for token in re.split(r"[\s,;.]+", text):
        if not token:
            continue
        plain = re.fullmatch(r"[+-]?\d+", token)
        if plain:
            word.append(int(token))
            continue
        named = re.fullmatch(r"[sσ](\d+)(\^?\(?(-?1)\)?)?", token)
        if named:
            index = int(named.group(1))
            word.append(-index if named.group(3) == "-1" else index)
            continue
        raise ValueError(f"Cannot read {token!r} as a generator.")
    if any(g == 0 for g in word):
        raise ValueError("Generators are numbered from 1.")
    return word
