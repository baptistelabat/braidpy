import pytest

from braidpy.utils import (
    PositiveFloat,
    PositiveInt,
    StrictlyPositiveFloat,
    StrictlyPositiveInt,
    int_to_subscript,
    int_to_superscript,
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


def test_a_lazy_module_is_imported_when_first_used():
    from braidpy.utils import lazy_module

    code = (
        "import sys; from braidpy.utils import lazy_module\n"
        "colorsys = lazy_module('colorsys')\n"
        "before = 'colorsys' in sys.modules\n"
        "colorsys.hsv_to_rgb(0, 0, 0)\n"
        "print(before, 'colorsys' in sys.modules)"
    )
    assert _run(code) == "False True"
    assert lazy_module("math").pi == pytest.approx(3.14159, abs=1e-5)


def test_braids_are_made_without_loading_what_draws_them():
    """Plotly, matplotlib and imageio only draw; sympy and math_braid are
    slow to import, and only some properties need them.  Making braids —
    a word's strands, a disk braid, a machine's — loads none of them: in a
    browser, through Pyodide, they would be tens of megabytes and seconds."""
    code = (
        "import sys\n"
        "from braidpy.braid import Braid\n"
        "from braidpy.take_off import braid_word_trajectories, lay_yarns,"
        " kumihimo_braid, tighten_yarns\n"
        "from braidpy.solid_sinnets_catalog import abok_3042\n"
        "from braidpy.ashley_solid_sinnet import sinnet_to_mobidai\n"
        "from braidpy.take_off import mobidai_braid\n"
        "from braidpy.horn_gear.examples import tubular_braid_8\n"
        "from braidpy.horn_gear.take_off import yarn_paths\n"
        "paths = lay_yarns(braid_word_trajectories(Braid([1, -2], 3)),"
        " yarn_diameter=0.4)\n"
        "tighten_yarns(paths, yarn_diameter=0.4, iterations=1)\n"
        "kumihimo_braid('SR', 0.1, n_strands=8, iterations=1)\n"
        "mobidai_braid(sinnet_to_mobidai(abok_3042), 0.1, n_cycles=1, iterations=1)\n"
        "yarn_paths(tubular_braid_8(), n_steps=4)\n"
        "print([m for m in ('plotly', 'matplotlib', 'imageio', 'sympy', 'math_braid')"
        " if m in sys.modules])"
    )
    assert _run(code) == "[]"


def _run(code: str) -> str:
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()
