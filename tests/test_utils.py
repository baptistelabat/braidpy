import pytest

from braidpy.utils import (
    int_to_superscript,
    int_to_subscript,
    PositiveFloat,
    PositiveInt,
    StrictlyPositiveFloat,
    StrictlyPositiveInt,
)


def test_int_to_superscript():
    # Examples:
    assert "t" + int_to_superscript(-1) == "t⁻¹"
    assert "t" + int_to_superscript(2) == "t²"
    assert "t" + int_to_superscript(-12) == "t⁻¹²"
    assert "t" + int_to_superscript(345) == "t³⁴⁵"


def test_int_to_subscript():
    # Examples
    assert "x" + int_to_subscript(2) == "x₂"
    assert "a" + int_to_subscript(-13) == "a₋₁₃"
    assert "i" + int_to_subscript(456) == "i₄₅₆"


def test_types():
    PositiveFloat(1)
    PositiveInt(1)
    StrictlyPositiveFloat(1)
    StrictlyPositiveInt(1)

    with pytest.raises(ValueError):
        PositiveFloat(-1)
    with pytest.raises(ValueError):
        PositiveInt(-1)
    with pytest.raises(ValueError):
        StrictlyPositiveFloat(-1)
    with pytest.raises(ValueError):
        StrictlyPositiveInt(-1)

    PositiveFloat(0)
    PositiveInt(0)
    with pytest.raises(ValueError):
        StrictlyPositiveFloat(0)
    with pytest.raises(ValueError):
        StrictlyPositiveInt(0)

    assert PositiveFloat(1.5) == 1.5

    assert PositiveInt(1.5) == 1
    assert StrictlyPositiveFloat(1.5) == 1.5
    assert StrictlyPositiveInt(1.5) == 1
