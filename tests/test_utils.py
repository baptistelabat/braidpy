from braidpy.utils import int_to_superscript, int_to_subscript


def test_int_to_superscript():
    # Examples:
    assert "t" + int_to_superscript(-1) =="t⁻¹"
    assert "t" + int_to_superscript(2) =="t²"
    assert "t" + int_to_superscript(-12) =="t⁻¹²"
    assert "t" + int_to_superscript(345) =="t³⁴⁵"

def test_int_to_subscript():
    # Examples
    assert "x" + int_to_subscript(2) =="x₂"
    assert "a" + int_to_subscript(-13) =="a₋₁₃"
    assert "i" + int_to_subscript(456) =="i₄₅₆"