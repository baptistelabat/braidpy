# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: braid_catalog.py
Description: A catalog of different remarkable braids
Authors: Baptiste Labat
Created: 2025-05-30
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from braidpy import Braid
from braidpy.artin_generators import a
from braidpy.braid import slide_strand, weave_strand
from braidpy.utils import StrictlyPositiveInt
import braidpy.braid
from typing import Tuple


def garside_half_twist_braid(n_strands: StrictlyPositiveInt) -> braidpy.braid.Braid:
    """
    Compute the Garside half twist braid also known as Garside element ∆n or (simply ∆ if n=n_strands-1)
    ∆² is known to generate the "center" of the braid group Bn+1.
    This is the biggest simple element.

    It is sometimes called fundamental braid.
    It can be obtained by recursion ∆n = σ1σ2...σn−1∆n−1


    Demi-vrille

    Composition of half_twist is giving a "torsade"

    Args:
        n_strands(StrictlyPositiveInt): number of strands

    Returns:
        Braid
    """

    b = a(0, n_strands)
    return b.half_twist()


def full_twist_braid(n_strands: StrictlyPositiveInt) -> braidpy.braid.Braid:
    """
    Compute the full twist braid ∆n² which is the square of Garside half twist braid
    ∆n
    It is known to generate the "center" of the braid group Bn.

    Vrille

    Composition of twist is giving a "torsade"

    Args:
        n_strands(StrictlyPositiveInt): number of strands

    Returns:
        Braid
    """

    b = a(0, n_strands)
    return b.full_twist()


def flat3() -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic braid with 3 strands going above central braid

    ABOK 2965: "FLAT, ENGLISH, ORDINARY or COMMON SINNET is the plat or
    braid seen in schoolgirl pigtails. It is made of three strands and is the
    simplest possible plat.
    To make: Secure three strands together and make the end fast
    to a hook or nail. Hold two strands in the right hand and one in the
    left. Bring the outer right strand down across its sister strand and lay
    it parallel to and below the single left strand. Now bring the upper
    Ie ft strand down across its sister strand and lay it parallel to and
    below the single right strand. Repeat alternately"

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 3
    step = Braid(1, n)
    b = (step * step.flip()) ** n
    b.draw()
    return b, n


def inverted_flat3() -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic braid with 3 strands going below central braid

    ABOK 2966: "Possibly a quicker but less usual way to make this plat is -
    to pass the strands at the back, employing only the first and second
    fingers and the thumbs"

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 3
    step = Braid(-1, n)
    b = step * step.flip()
    b.draw()
    (b**n).draw()
    return b, n


def square4() -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic round braid with 4 strands

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 4
    step = Braid((-1, -2, -2), n)
    b = step * step.flip()
    b.draw()
    print(" ")
    (b**n).draw()
    return b, n


def asymmetric_flat4() -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic flat braid with 4 strands

    https://www.youtube.com/watch?v=7lTFIzm9BLY

    ABOK 2969: "Unless for some special purpose, this method is usually
    limited to an odd number of strands, as with an even number of
    strands the sinnet is unsymmetrical. But I have seen the braid, made
    as if with three strands in the left hand and one in the right hand,
    as here pictured, used as edging on theater-seat upholstery. Of
    course it was machine-made."

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 4
    step = slide_strand(2).n(4) * a(-3)
    b = step
    b.draw()
    (b**n).draw()
    return b, n


def flat6() -> Tuple[braidpy.braid.Braid, int]:
    """
    This one is probably not unique !

    https://www.youtube.com/watch?v=ZHWlYBxL-mA

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 6
    # Initialisation in video ?
    # step1 = slide_strand(5).n(n).flip()
    # step2 = slide_strand(4, start_index=2).n(n)

    # Now loop
    step3 = slide_strand(int(n / 2), start_index=2).n(n).flip()
    step4 = slide_strand(int(n / 2)).n(n)  # "Ramener l'extrème gauche au centre"
    # step5 = slide_strand(int(n / 2), start_index=2).n(n)
    # step6 = slide_strand(int(n / 2)).flip().n(n)  # "Ramener l'extrème droite au centre"
    # step7 = slide_strand(int(n / 2), start_index=2).n(n).flip()
    # step8 = slide_strand(int(n / 2)).n(n)
    # step2 = slide_strand(int(n / 2), start_index=2).n(n)

    step = step3 * step4
    step.draw()
    b = step * step.flip()
    (b**n).draw()
    return b, n


def regular_flat6() -> Tuple[braidpy.braid.Braid, int]:
    """
    https://www.youtube.com/watch?v=J65kCzm_BtI

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 6
    step1 = weave_strand(int(n / 2)).n(n)
    step2 = weave_strand(int(n / 2) - 1, sign=-1).n(n).flip()

    step1.draw()
    step2.draw()
    b = step1 * step2
    (b**n).draw()
    return b, n


def double_flat3(parallel: bool = True):
    """
    if parallel = False
    ABOK 2971: "If the same method of turning edges is applied where units
    of two or three parallel round cords are used, instead of single
    strands, a distinctive sinnet results"

    if parallel = True
    ABOK 2972: "In this sinnet the strands are double and parallel. The effect
    is very different from the last, in which the edges were turned."
    """
    parallel = False
    n = 3
    n_multiple = 2
    if parallel:
        step = a(0)
    else:
        step = a(1)
    for i in range(n_multiple):
        for j in range(n_multiple):
            step = step * a(1 + n_multiple - 1 - i + j)
    step = step.n(n * n_multiple)
    b = (step * step.flip()) ** n
    b.draw()
    return b, n


def flat5() -> Tuple[braidpy.braid.Braid, int]:
    """
    https://www.youtube.com/watch?v=uRy4wvJwSWA

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 5
    step1 = slide_strand(int((n - 1) / 2)).n(n) * a(2)
    step2 = slide_strand(int((n + 1) / 2)).n(n).flip()
    step = step1 * step2
    step.draw()
    (step**n).draw()
    return step, n


def flat_sinnet5():
    """
    ABOK 2967: "With more than three strands it is well to secure the strands
    in a straight line. Two pencils and two elastic bands are sufficient
    apparatus. FLAT SI~NET may be made with any odd number of
    strands in the way already described. The outer strands are moved
    alternately, and the tension is correctly and evenly arranged as each
    strand is passed".

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 5
    step = slide_strand(int((n - 1) / 2)).n(n)
    b = (step * step.flip()) ** n
    b.draw()
    return b, n


def flat_sinnet7():
    """
    ABOK 2968: "Seven strands is about the practical limit of the method.
    Beyond that there is difficulty in keeping it even. Even if a degree
    of success is achieved, a very little rough treatment will cause it to
    distort."

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 7
    step = slide_strand(int((n - 1) / 2)).n(n)
    b = (step * step.flip()) ** n
    b.draw()
    return b, n
