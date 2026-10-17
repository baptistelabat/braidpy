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
from typing import Any, Dict, List, Tuple

from braidpy.catalogue import Entry

"""
In flat braid all the strands follow the same track
In tubular braid, the strands follow two separate, though interwoven tracks
https://loopbraider.com/track-plans/
"""


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


def flat3(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
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

    https://www.animatedknots.com/three-strand-braid-knot

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 3
    step = Braid(1, n)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def inverted_flat3(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic braid with 3 strands going below central braid. Also known as dutch braid

    ABOK 2966: "Possibly a quicker but less usual way to make this plat is -
    to pass the strands at the back, employing only the first and second
    fingers and the thumbs"

    https://www.animatedknots.com/three-strand-braid-knot-alt

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 3
    step = Braid(-1, n)
    b = step * step.flip()
    if draw:
        b.draw()
        (b**n).draw()
    return b, n


def square4(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic round braid with 4 strands

    https://www.animatedknots.com/four-strand-square-sinnet-knot

    ABOK 2999. "SQUARE SINNET of four strands. Used for lanyards, whips, whiplashes, quirts and leashes.
    With strands of two colors, arranged as pictured, the two colors helix around the sinnet,
    giving a barber-pole or candy-twist effect.
    The sinnet is made in two movements.
    First, take the top left strand, bring it around to the back of the other strands and then from back to front
    between the opposing strands. Finally lay it beside its sister strand into the lower position at the left.
    Second, take the right upper strand, bring it around to the back of the other strands and
    then from back to front between the opposing strands. Finally lay it beside its sister strand into the lower
    position at the right. In this size, this sinnet, although made by the SQUARE SINNET method,
    is identical with ROUND SINNET of four strands."

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 4
    step = Braid((-1, -2, -2), n)
    b = step * step.flip()
    if draw:
        b.draw()
        print(" ")
        (b**n).draw()
    return b, n


def asymmetric_flat4(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    Basic flat braid with 4 strands

    https://www.youtube.com/watch?v=7lTFIzm9BLY

    ABOK 2969: "Unless for some special purpose, this method is usually
    limited to an odd number of strands, as with an even number of
    strands the sinnet is unsymmetrical. But I have seen the braid, made
    as if with three strands in the left hand and one in the right hand,
    as here pictured, used as edging on theater-seat upholstery. Of
    course it was machine-made."

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 4
    step = slide_strand(2).n(4) * a(-3)
    b = step
    if draw:
        b.draw()
        (b**n).draw()
    return b, n


def flat6(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    This one is probably not unique !

    https://www.youtube.com/watch?v=ZHWlYBxL-mA

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

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
    if draw:
        step.draw()
    b = step * step.flip()
    if draw:
        (b**n).draw()
    return b, n


def regular_flat6(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    https://www.youtube.com/watch?v=J65kCzm_BtI

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 6
    step1 = weave_strand(int(n / 2)).n(n)
    step2 = weave_strand(int(n / 2) - 1, sign=-1).n(n).flip()

    if draw:
        step1.draw()
        step2.draw()
    b = step1 * step2
    if draw:
        (b**n).draw()
    return b, n


def double_flat3(parallel: bool = True, draw: bool = True):
    """
    if parallel = False
    ABOK 2971: "If the same method of turning edges is applied where units
    of two or three parallel round cords are used, instead of single
    strands, a distinctive sinnet results"

    if parallel = True
    ABOK 2972: "In this sinnet the strands are double and parallel. The effect
    is very different from the last, in which the edges were turned."

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    parallel = False
    n = 3
    n_multiple = 2
    step: Braid = a(0) if parallel else a(1)
    for i in range(n_multiple):
        for j in range(n_multiple):
            step = step * a(1 + n_multiple - 1 - i + j)
    step = step.n(n * n_multiple)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def weave3(draw: bool = True):
    """
    This a 3 strands braid were 2 braids are running parallel while the third one is weaving them

    ABOK 2973:  "The number of sinnets that are possible with three strands
    only seem very limited. Three are given on these two facing pages."

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """

    n = 3
    step = a(1) * a(-2).n(n)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def abok_2974(draw: bool = True):
    """
    2974. With four strands the horizon is somewhat widened.

    https://www.animatedknots.com/four-strand-sinnet-knot-2974

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:

    """
    n = 2
    step = Braid([-1, -3, 2, 2], 4)
    if draw:
        step.draw()
        (step**n).draw()
    return step, n


def flat5(draw: bool = True) -> Tuple[braidpy.braid.Braid, int]:
    """
    https://www.youtube.com/watch?v=uRy4wvJwSWA

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 5
    step1 = slide_strand(int((n - 1) / 2)).n(n) * a(2)
    step2 = slide_strand(int((n + 1) / 2)).n(n).flip()
    step = step1 * step2
    if draw:
        step.draw()
        (step**n).draw()
    return step, n


def flat_sinnet5(draw: bool = True):
    """
    ABOK 2967: "With more than three strands it is well to secure the strands
    in a straight line. Two pencils and two elastic bands are sufficient
    apparatus. FLAT SI~NET may be made with any odd number of
    strands in the way already described. The outer strands are moved
    alternately, and the tension is correctly and evenly arranged as each
    strand is passed".

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 5
    step = slide_strand(int((n - 1) / 2)).n(n)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def flat_sinnet7(draw: bool = True):
    """
    ABOK 2968: "Seven strands is about the practical limit of the method.
    Beyond that there is difficulty in keeping it even. Even if a degree
    of success is achieved, a very little rough treatment will cause it to
    distort."

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 7
    step = slide_strand(int((n - 1) / 2)).n(n)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def triangle_sinnet_9():
    """
    ABOK3057
    https://craftdesignonline.com/design/9-strand-triangle-sinnet-1/

    ABOK3058
    https://craftdesignonline.com/design/9-strand-triangle-sinnet-2/

    Returns:

    """


def triangle_sinnet_10():
    """
    ABOK3045
    https://craftdesignonline.com/design/10-strand-triangle-sinnet/

    Returns:

    """


"""
14-strands 7-loop D-shaped (unorthodox)
https://loopbraider.com/2015/04/21/uo-dshaped-7tut/
"""

"""
16-strands interlaced french sinnet
https://www.youtube.com/watch?v=we4seysYqrk
"""
"""
23-strand interlaced french sinnet
https://www.youtube.com/watch?v=HY7mis6Ss60
"""

"""
ABOK #2996
https://www.youtube.com/watch?v=gXl5dX844sg
"""
"""
ABOK #3021
https://www.youtube.com/watch?v=G0BFWYYVj7M
"""

"""
ABOK2979
https://www.paracordguild.com/french-sinnet-abok-2979-tutorial/

"""
"""
ABOK3044
https://craftdesignonline.com/design/8-strand-triangle-sinnet/
"""

"""
ABOK3073
https://craftdesignonline.com/design/20-strand-square-sinnet/
"""

"""
17-Strand Half Round Sinnet
ABOK3054
https://craftdesignonline.com/design/17-strand-half-round-sinnet/
"""

"""
7 strands braid (not exactly a kumihimo) with 8 slots mobidai
https://raft.net/wp-content/uploads/2020/08/PGS-Kumihimo.pdf
"""

"""
16 strands kumihimo
https://youtu.be/cGFLqDZTtoQ?si=WrbbVFJ50fQ0ELE5&t=92
"""


# ------------------------------------------------------------ as braid words

# More braids worth trying as braid words: Braid Studio offers them as
# examples after the catalogue's (see :func:`word_examples`).
WORD_EXAMPLES: List[Dict[str, Any]] = [
    {"word": "1 2 3", "n_strands": 4, "repeat": 12, "title": "Twist"},
    {"word": "1 -2 3 -2", "n_strands": 4, "repeat": 4, "title": "Four-strand flat"},
    {"word": "1 1 1", "n_strands": 2, "repeat": 8, "title": "Two-ply"},
    {
        "layout": "ring",
        "word": "4",
        "n_strands": 3,
        "repeat": 36,
        "title": "Rope, as a ring word",
    },
]

# The braids above that are a braid word, built without drawing them, as
# every catalogue lists its braids (:mod:`braidpy.catalogue`).
CATALOGUE: Dict[str, Entry[Braid]] = {
    "flat3": Entry(
        "Plait, or flat sinnet of 3 (ABOK 2965)",
        lambda: flat3(draw=False)[0],
        "The Ashley Book of Knots, #2965",
    ),
    "inverted_flat3": Entry(
        "Dutch braid of 3 (ABOK 2966)",
        lambda: inverted_flat3(draw=False)[0],
        "The Ashley Book of Knots, #2966",
    ),
    "weave3": Entry(
        "Weave of 3 (ABOK 2973)",
        lambda: weave3(draw=False)[0],
        "The Ashley Book of Knots, #2973",
    ),
    "double_flat3": Entry(
        "Double flat sinnet of 3 (ABOK 2971)",
        lambda: double_flat3(draw=False)[0],
        "The Ashley Book of Knots, #2971",
    ),
    "square4": Entry(
        "Square sinnet of 4 (ABOK 2999)",
        lambda: square4(draw=False)[0],
        "The Ashley Book of Knots, #2999",
    ),
    "asymmetric_flat4": Entry(
        "Asymmetric flat sinnet of 4 (ABOK 2969)",
        lambda: asymmetric_flat4(draw=False)[0],
        "The Ashley Book of Knots, #2969",
    ),
    "abok_2974": Entry(
        "Four-strand sinnet (ABOK 2974)",
        lambda: abok_2974(draw=False)[0],
        "The Ashley Book of Knots, #2974",
    ),
    "flat5": Entry("Flat braid of 5", lambda: flat5(draw=False)[0]),
    "flat_sinnet5": Entry(
        "Flat sinnet of 5 (ABOK 2967)",
        lambda: flat_sinnet5(draw=False)[0],
        "The Ashley Book of Knots, #2967",
    ),
    "flat6": Entry("Flat braid of 6", lambda: flat6(draw=False)[0]),
    "regular_flat6": Entry(
        "Regular flat braid of 6", lambda: regular_flat6(draw=False)[0]
    ),
    "flat_sinnet7": Entry(
        "Flat sinnet of 7 (ABOK 2968)",
        lambda: flat_sinnet7(draw=False)[0],
        "The Ashley Book of Knots, #2968",
    ),
}


# An example shows at least so many crossings.
_FEWEST_CROSSINGS = 12


def word_examples() -> List[Dict[str, Any]]:
    """Braids to try as braid words, as plain data: each of
    :data:`CATALOGUE` reduced to the word it repeats, then
    :data:`WORD_EXAMPLES`.  A braid is repeated as many times as brings
    every strand home, twice or more: at least :data:`_FEWEST_CROSSINGS`
    crossings.

    Returns:
        Per braid, its ``word``, ``n_strands``, ``repeat`` and ``title``; a
        ring word's ``layout`` too.
    """
    from braidpy.pure_braid import closing_repeats, repeating_unit

    examples: List[Dict[str, Any]] = []
    for entry in CATALOGUE.values():
        braid = entry.make()
        unit = repeating_unit(braid.generators)
        n_strands = braid.n_strands
        home = closing_repeats(Braid(tuple(unit), n_strands), limit=None) or 1
        times = max(2, -(-_FEWEST_CROSSINGS // (len(unit) * home)))
        examples.append(
            {
                "word": " ".join(str(g) for g in unit),
                "n_strands": n_strands,
                "repeat": home * times,
                "title": entry.title,
            }
        )
    return examples + [dict(example) for example in WORD_EXAMPLES]
