from braidpy.artin_generator import a


def garside_half_twist_braid(n_strands):
    """
    Compute the Garside half twist braid also known as Garside element ∆n
    ∆n² is known to generate the "center" of the braid group Bn.

    It is sometimes called fundamental braid. This can
    It can be obtained by recursion ∆n = σ1σ2...σn−1∆n−1


    Demi-vrille

    Composition of half_twist is giving a "torsade"

    Args:
        n_strands:

    Returns:

    """

    b = a(0, n_strands)
    return b.half_twist()


def full_twist_braid(n_strands):
    """
    Compute the full twist braid ∆n² which is the square of Garside half twist braid
    ∆n
    It is known to generate the "center" of the braid group Bn.

    Vrille

    Composition of twist is giving a "torsade"

    Args:
        n_strands:

    Returns:

    """

    b = a(0, n_strands)
    return b.full_twist()
