import pytest

from braidpy.handles_reduction import dehornoy_reduce_core, HandleReductionMode


def test_dehornoy_reduce_core():
    reduced, sign = dehornoy_reduce_core(gens=[])
    assert reduced == []
    assert sign == 0

    reduced, sign = dehornoy_reduce_core(gens=[0])
    assert reduced == []
    assert sign == 0

    reduced, sign = dehornoy_reduce_core(gens=[], mode="COMPARE")
    assert reduced == []
    assert sign == 0

    reduced, sign = dehornoy_reduce_core(gens=[0], mode="COMPARE")
    assert reduced == []
    assert sign == 0

    reduced, sign = dehornoy_reduce_core(gens=[1])
    assert reduced == [1]
    assert sign == 1

    reduced, sign = dehornoy_reduce_core(gens=[-1])
    assert reduced == [-1]
    assert sign == -1

    # BBAAbbaa should give BBAbaBbaBa, then BBbaBBbaBa, then BaBBbaBa, then BaBaBa
    reduced, sign = dehornoy_reduce_core(
        gens=[-2, -2, -1, -1, 2, 2, 1, 1]
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert reduced == [-2, 1, -2, 1, -2, 1]
    assert sign == 1

    reduced, sign = dehornoy_reduce_core(
        gens=[-2, -2, -1, -1, 2, 2, 1, 1], mode=HandleReductionMode.COMPARE
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert sign == 1
    assert len(reduced) > 6  # Check that computation did not go as far as in FULL mode

    # abaCBCABAcbca should give bbCaBBc (page 165)
    reduced, sign = dehornoy_reduce_core(
        gens=[1, 2, 1, -3, -2, -3, -1, -2, -1, 3, 2, 3, 1], mode="FULL"
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert reduced == [2, 2, -3, 1, -2, -2, 3]
    assert sign == 1

    with pytest.raises(ValueError):
        dehornoy_reduce_core(gens=[0.5])
