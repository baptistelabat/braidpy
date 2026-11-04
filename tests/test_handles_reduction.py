# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from braidpy.handles_reduction import HandleReductionMode, dehornoy_reduce_core


def test_dehornoy_reduce_core():
    results = dehornoy_reduce_core(gens=[])
    assert results.generators == []
    assert results.sign == 0

    results = dehornoy_reduce_core(gens=[0])
    assert results.generators == []
    assert results.sign == 0

    results = dehornoy_reduce_core(gens=[], mode="COMPARE")
    assert results.generators == []
    assert results.sign == 0

    results = dehornoy_reduce_core(gens=[0], mode="COMPARE")
    assert results.generators == []
    assert results.sign == 0

    results = dehornoy_reduce_core(gens=[1])
    assert results.generators == [1]
    assert results.sign == 1

    results = dehornoy_reduce_core(gens=[-1])
    assert results.generators == [-1]
    assert results.sign == -1

    # BBAAbbaa should give BBAbaBbaBa, then BBbaBBbaBa, then BaBBbaBa, then BaBaBa
    results = dehornoy_reduce_core(
        gens=[-2, -2, -1, -1, 2, 2, 1, 1]
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert results.generators == [-2, 1, -2, 1, -2, 1]
    assert results.sign == 1

    results = dehornoy_reduce_core(
        gens=[-2, -2, -1, -1, 2, 2, 1, 1], mode=HandleReductionMode.COMPARE
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert results.sign == 1
    assert (
        len(results.generators) > 6
    )  # Check that computation did not go as far as in FULL mode

    # abaCBCABAcbca should give bbCaBBc (page 165)
    results = dehornoy_reduce_core(
        gens=[1, 2, 1, -3, -2, -3, -1, -2, -1, 3, 2, 3, 1], mode="FULL"
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert results.generators == [2, 2, -3, 1, -2, -2, 3]
    assert results.sign == 1

    with pytest.raises(ValueError):
        dehornoy_reduce_core(gens=[0.5])
