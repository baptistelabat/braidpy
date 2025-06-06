from typing import List


def braidword_alpha_to_numeric(braidword: str) -> List[int]:
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
