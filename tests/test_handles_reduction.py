from braidpy.handles_reduction import dehornoy_reduce_core


def test_dehornoy_reduce_core():
    # BBAAbbaa should give BBAbaBbaBa, then BBbaBBbaBa, then BaBBbaBa, then BaBaBa
    # reduced, _ =dehornoy_reduce_core(gens= [-2, -2 , -1, -1, 2, 2, 1, 1]) # Example from "Le calcul des tresses 1.2.3 page 164
    # assert reduced == [-2, 1, -2, 1, -2, 1]

    # abaCBCABAcbca should give bbCaBBc (page 165)
    reduced, _ = dehornoy_reduce_core(
        gens=[1, 2, 1, -3, -2, -3, -1, -2, -1, 3, 2, 3, 1]
    )  # Example from "Le calcul des tresses 1.2.3 page 164
    assert reduced == [2, 2, -3, 1, -2, -2, 3]
