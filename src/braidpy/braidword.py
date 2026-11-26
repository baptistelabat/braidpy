# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braid words read from text, written in letters (``aB``), as signed
numbers (``1 -2``) or as named generators (``s1 s2^-1``): braidpy's one
reader of them (:func:`parse_word`)."""

import re


def braidword_alpha_to_numeric(braidword: str) -> list[int]:
    """
    Convert an alphabetical braid word to its numerical representation.

    Each lowercase letter represents a braid generator σ_i, where:
        - 'a' → σ₁ → 1
        - 'b' → σ₂ → 2
        - ...

    Each uppercase letter represents the inverse generator σ_i⁻¹:
        - 'A' → σ₁⁻¹ → -1
        - 'B' → σ₂⁻¹ → -2
        - ...

    Special character # can be used for neutral element

    Args:
        braidword (str): A string of alphabetical characters representing the braid word.
                         Must contain only letters a–z and A–Z or character #

    Returns:
        List[int]: The numerical representation of the braid word.

    Raises:
        ValueError: If the input contains non-alphabetical characters.

    Example:
        >>> braidword_alpha_to_numeric("abAB")
        [1, 2, -1, -2]
    """
    numeric_word: list[int] = []
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


def parse_word(text: str) -> list[int]:
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
    word: list[int] = []
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


def parse_band_word(text: str) -> list[tuple[int, int]]:
    """A braid word in band generators
    (:mod:`braidpy.band_canonical_form`), as band letters.

    Reads ``4:1 2:1 1:3`` (or with commas): ``t:s`` for ``a_ts``, strands
    ``t > s`` crossing in front of those between, and ``s:t`` for its
    inverse.

    Args:
        text: The word.

    Returns:
        The letters, ``(t, s)`` or ``(s, t)``; empty for an empty word.

    Raises:
        ValueError: If a letter is not two strands apart from 1 on.
    """
    letters: list[tuple[int, int]] = []
    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        pair = re.fullmatch(r"(\d+):(\d+)", token)
        if pair is None:
            raise ValueError(f"Cannot read {token!r} as a band letter: write 4:1.")
        first, second = int(pair.group(1)), int(pair.group(2))
        if first == second or min(first, second) < 1:
            raise ValueError(
                f"A band letter crosses two strands from 1 on, not {token!r}."
            )
        letters.append((first, second))
    return letters
