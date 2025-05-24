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


# Examples:
print("t" + int_to_superscript(-1))  # t⁻¹
print("t" + int_to_superscript(2))  # t²
print("t" + int_to_superscript(-12))  # t⁻¹²
print("t" + int_to_superscript(345))  # t³⁴⁵
print("t" + int_to_superscript(-1000))

# Examples
print("x" + int_to_subscript(2))  # x₂
print("a" + int_to_subscript(-13))  # a₋₁₃
print("i" + int_to_subscript(456))  # i₄₅₆
