# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A catalogue of remarkable braids, as words."""

import re
from dataclasses import dataclass
from typing import Any, Literal

import braidpy.braid
from braidpy import Braid
from braidpy.artin_generators import a
from braidpy.braid import slide_strand, weave_strand
from braidpy.catalog import Entry, Link, ashley
from braidpy.utils import StrictlyPositiveInt

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


def flat3(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
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


def inverted_flat3(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    Basic braid with 3 strands going below central braid. Also known as dutch braid

    ABOK 2966: "Possibly a quicker but less usual way to make this plat is -
    to pass the strands at the back, employing only the first and second
    fingers and the thumbs"

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


def square4(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    Basic round braid with 4 strands

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


def asymmetric_flat4(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    Basic flat braid with 4 strands

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


def flat6(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    This one is probably not unique !

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


def regular_flat6(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    Regular flat braid with 6 strands.

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


def double_flat3(
    parallel: bool = False, draw: bool = True
) -> tuple[braidpy.braid.Braid, int]:
    """
    ABOK 2971: "If the same method of turning edges is applied where units
    of two or three parallel round cords are used, instead of single
    strands, a distinctive sinnet results"

    ABOK 2972, its parallel twin, is not made yet: "In this sinnet the
    strands are double and parallel. The effect is very different from the
    last, in which the edges were turned."

    Args:
        parallel: ABOK 2972 rather than 2971: not made yet.
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    if parallel:
        raise NotImplementedError("ABOK 2972, the parallel double flat sinnet")
    n = 3
    n_multiple = 2
    step: Braid = a(1)
    for i in range(n_multiple):
        for j in range(n_multiple):
            step = step * a(1 + n_multiple - 1 - i + j)
    step = step.n(n * n_multiple)
    b = (step * step.flip()) ** n
    if draw:
        b.draw()
    return b, n


def weave3(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    A braid of 3 strands where 2 strands run parallel while the third one
    weaves through them.

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


def abok_2974(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    2974. With four strands the horizon is somewhat widened.

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    n = 2
    step = Braid([-1, -3, 2, 2], 4)
    if draw:
        step.draw()
        (step**n).draw()
    return step, n


def flat5(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    Flat braid with 5 strands.

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


def flat_sinnet5(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """
    ABOK 2967: "With more than three strands it is well to secure the strands
    in a straight line. Two pencils and two elastic bands are sufficient
    apparatus. FLAT SINNET may be made with any odd number of
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


def flat_sinnet7(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
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
ABOK2979
https://www.paracordguild.com/french-sinnet-abok-2979-tutorial/

"""
"""
7 strands braid (not exactly a kumihimo) with 8 slots mobidai
https://raft.net/wp-content/uploads/2020/08/PGS-Kumihimo.pdf
"""

"""
16 strands kumihimo
https://youtu.be/cGFLqDZTtoQ?si=WrbbVFJ50fQ0ELE5&t=92
"""


# ------------------------------------------------------------ Ashley's plats

# A lead's path, as Ashley gives it: "u3 o1", under three strands, then over one.
_PATH = re.compile(r"\s*([ou])(\d+)")


def _path(text: str) -> list[str]:
    """A lead's path, a letter a strand passed: ``"u2 o1"`` is u, u, o."""
    passed: list[str] = []
    at = 0
    for match in _PATH.finditer(text):
        if match.start() != at:
            break
        passed += [match.group(1)] * int(match.group(2))
        at = match.end()
    if at != len(text.rstrip()) or not passed:
        raise ValueError(f"A lead is over and under so many strands: not {text!r}.")
    return passed


@dataclass(frozen=True)
class AshleyPlat:
    """A sinnet plaited in the hands as *The Ashley Book of Knots* says, its
    strands held in two groups, the top strand of each led in turn.

    Two ways of leading a strand, as the book's plat sinnets have them:

    - ``"plat"`` (#2976–#2998, and Smith's square sinnets #3017–#3019): the
      top strand is led to the centre, over and under its sisters as its path
      says, and joins the other group, lowest in it;
    - ``"square"`` (the square sinnet's method, #2999–#3014): the top strand
      goes round behind its sisters and behind the opposing strands, comes
      forward between two of them — its path as long as the opposing
      strands it passed, counted from the bottom — and comes back along its
      path, over and under them, to lie lowest in its own group.

    The strands are numbered from the left, the left group first; a strand
    led over its neighbour to the right is ``σᵢ``, as everywhere in braidpy.

    Args:
        shape: What the book calls it: "flat", "French", "square"...
        n_strands: Strands.
        n_left: Strands held in the left hand at the start.
        leads: Each lead's path, the left group's top strand first unless
            ``first`` says otherwise, then the right's, in turn.
        method: How a strand is led.
        first: The group whose strand is led first.
    """

    shape: str
    n_strands: int
    n_left: int
    leads: tuple[str, ...]
    method: Literal["plat", "square"] = "plat"
    first: Literal["left", "right"] = "left"

    def braid(self) -> Braid:
        """The braid of one round of the leads.

        Returns:
            The braid.

        Raises:
            ValueError: If a lead passes more strands than it can, or the
                groups are not as they started after the round.
        """
        n, left, word = self.n_strands, self.n_left, []
        side = self.first
        for lead in self.leads:
            passed = _path(lead)
            right = n - left
            if self.method == "plat":
                sisters = (left if side == "left" else right) - 1
                if len(passed) != sisters:
                    raise ValueError(
                        f"{lead!r} passes {len(passed)} strands, its {sisters} sisters."
                    )
                if side == "left":
                    word += [i if k == "o" else -i for i, k in enumerate(passed, 1)]
                    left -= 1
                else:
                    places = range(n - 1, left, -1)
                    word += [-i if k == "o" else i for i, k in zip(places, passed)]
                    left += 1
            else:
                opposing = right if side == "left" else left
                if len(passed) > opposing:
                    raise ValueError(
                        f"{lead!r} passes {len(passed)} of {opposing} opposing strands."
                    )
                if side == "left":
                    # Behind its sisters and the opposing strands, then back.
                    at = left + len(passed)
                    word += [-i for i in range(1, at)]
                    for k in passed:
                        word.append(-(at - 1) if k == "o" else at - 1)
                        at -= 1
                else:
                    at = left + 1 - len(passed)
                    word += list(range(n - 1, at - 1, -1))
                    for k in passed:
                        word.append(at if k == "o" else -at)
                        at += 1
            side = "right" if side == "left" else "left"
        if left != self.n_left:
            raise ValueError("The groups are not as they started after the leads.")
        return Braid(tuple(word), n)


#: The plat sinnets of *The Ashley Book of Knots* (chapter 38) made as its
#: text says, by number.  Left out: those of doubled strands (#2972,
#: #2978, coachwhipping #3015, #3016), the "trick" sinnet #2993, #2979
#: (#2976 made another way, the same braid), and the round sinnets worked
#: turning in the hand (#3021 on), which are ring words.
ASHLEY_PLATS: dict[int, AshleyPlat] = {
    2976: AshleyPlat("French", 7, 4, ("u1 o1 u1", "u1 o1 u1")),
    2977: AshleyPlat("French", 6, 3, ("o1 u1", "u1 o1 u1")),
    2980: AshleyPlat("flat", 8, 5, ("u3 o1", "o3")),
    2981: AshleyPlat("flat", 6, 3, ("o1 u1", "u1 o2")),
    2982: AshleyPlat("flat", 7, 5, ("u3 o1", "u1 o1")),
    2983: AshleyPlat("flat", 7, 4, ("u2 o1", "u2 o1")),
    2984: AshleyPlat("flat", 7, 5, ("u2 o2", "o2")),
    2985: AshleyPlat("flat", 9, 5, ("u2 o2", "u2 o2")),
    2986: AshleyPlat("flat", 11, 6, ("u2 o3", "u2 o3")),
    2987: AshleyPlat("flat", 11, 6, ("u2 o2 u1", "u2 o2 u1")),
    2988: AshleyPlat("French", 5, 3, ("o2", "o2", "u2", "u2")),
    2989: AshleyPlat("duplex", 6, 4, ("o3", "o2", "u3", "u2")),
    2990: AshleyPlat("twill", 9, 5, ("u1 o3", "u1 o3", "u2 o2", "u2 o2")),
    2991: AshleyPlat("twill", 10, 5, ("o2 u2", "o2 u2 o1", "o2 u2", "o2 u3")),
    2992: AshleyPlat("twill", 10, 5, ("o1 u3", "o1 u3 o1", "o1 u3", "o1 u4")),
    2994: AshleyPlat("doubled-edge flat", 6, 4, ("o1 u2", "o2", "u1 o2", "u2")),
    2995: AshleyPlat("doubled-edge flat", 7, 4, ("o2 u1", "u1 o2", "u2 o1", "o1 u2")),
    2996: AshleyPlat(
        "doubled-edge flat", 8, 5, ("u1 o2 u1", "u1 o2", "o1 u2 o1", "o1 u2")
    ),
    2997: AshleyPlat(
        "doubled-edge flat", 10, 6, ("u2 o2 u1", "u2 o2", "o2 u2 o1", "o2 u2")
    ),
    2998: AshleyPlat(
        "doubled-edge flat",
        11,
        6,
        (
            "u1 o2 u1 o1",
            "u2 o1 u2",
            "o1 u1 o2 u1",
            "o1 u2 o1 u1",
            "o2 u1 o2",
            "u1 o1 u2 o1",
        ),
    ),
    3001: AshleyPlat("square", 8, 4, ("o2", "o2"), "square"),
    3002: AshleyPlat("square", 12, 6, ("o3", "o3"), "square", "right"),
    3003: AshleyPlat("half round", 6, 3, ("o1", "o1"), "square"),
    3004: AshleyPlat("half round", 8, 4, ("o1", "o1"), "square"),
    3005: AshleyPlat("half round", 10, 5, ("o2", "o2"), "square"),
    3006: AshleyPlat("half round", 8, 4, ("o1 u1", "o1 u1"), "square"),
    3007: AshleyPlat("ellipse", 8, 4, ("o1 u2", "o1 u1"), "square"),
    3008: AshleyPlat("ellipse", 6, 3, ("o2", "o1"), "square"),
    3009: AshleyPlat("ellipse", 8, 4, ("o3", "o1"), "square"),
    3010: AshleyPlat("ellipse", 10, 5, ("o3", "o2"), "square"),
    3011: AshleyPlat("round", 6, 3, ("o1 u1", "o1"), "square"),
    3012: AshleyPlat("round", 8, 4, ("o1 u1 o1", "o1 u1 o1"), "square"),
    3013: AshleyPlat("square", 5, 3, ("o1", "o2"), "square"),
    3014: AshleyPlat("square", 7, 4, ("o2", "o2"), "square"),
    3017: AshleyPlat("square", 4, 3, ("o2", "o1", "u2", "u1")),
    3018: AshleyPlat("square", 8, 5, ("o4", "o3", "u4", "u3")),
    3019: AshleyPlat("square", 12, 7, ("o6", "o5", "u6", "u5")),
}


# ------------------------------------------------------------ as braid words

#: The rectangular braid of fourteen strands, as the word it repeats.
#:
#: The fourteen places fall into two sets of seven that never mix: the
#: word's permutation is two 7-cycles, so seven repeats bring every strand
#: home.  The sets interleave across the face, one place of the first, then
#: two of the second, then two of the first: ABBAABBAABBAAB.  Thirty-two
#: crossings a repeat, as many one way as the other, so nothing twists.
RECTANGULAR_14 = (
    "2 -5 -9 7 -11 -3 13 1 -6 10 -8 4 -4 -10 -7 -12 "
    "-2 4 7 10 5 9 -7 -13 -1 11 3 -10 -4 6 8 12"
)


def rectangular14(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """The rectangular braid of fourteen strands (:data:`RECTANGULAR_14`).

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    from braidpy.braidword import parse_word

    b = Braid(tuple(parse_word(RECTANGULAR_14)), 14)
    if draw:
        b.draw()
    return b, 7


#: The rectangular braid of twenty strands, as the word it repeats.
#:
#: Forty-six crossings a repeat, as many one way as the other, and every
#: one of the nineteen crossing places used.  The twenty places fall into
#: two sets of ten that never mix — the word's permutation is two 10-cycles
#: — so ten repeats bring every strand home.  Wider than
#: :data:`RECTANGULAR_14` and not a wider copy of it: the sets interleave
#: as ABBABAABABBABAABABBA, in threes and pairs rather than evenly.
RECTANGULAR_20 = (
    "2 19 -4 -16 1 -10 -9 -11 10 3 17 -5 -15 -6 -14 -4 -16 -8 -12 5 15 -3 "
    "-17 9 11 -2 6 14 -18 7 13 -6 -14 17 3 8 12 7 13 -12 -1 -8 -19 5 15 18"
)


def rectangular20(draw: bool = True) -> tuple[braidpy.braid.Braid, int]:
    """The rectangular braid of twenty strands (:data:`RECTANGULAR_20`).

    Args:
        draw: Draw the braid as it is made (the default); False only builds it.

    Returns:
        Braid: the braid object describing the single step to realize the braid
        n: the number of iterations to get back to initial order of strands
    """
    from braidpy.braidword import parse_word

    b = Braid(tuple(parse_word(RECTANGULAR_20)), 20)
    if draw:
        b.draw()
    return b, 10


# More braids worth trying as braid words: Braid Studio offers them as
# examples after the catalogue's (see :func:`word_examples`).
WORD_EXAMPLES: list[dict[str, Any]] = [
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
# every catalogue lists its braids (:mod:`braidpy.catalog`).
CATALOG: dict[str, Entry[Braid]] = {
    "flat3": Entry(
        "Plait, or flat sinnet of 3 (ABOK 2965)",
        lambda: flat3(draw=False)[0],
        (
            ashley(2965),
            Link(
                "Animated Knots: three strand braid",
                "page",
                "https://www.animatedknots.com/three-strand-braid-knot",
            ),
        ),
    ),
    "inverted_flat3": Entry(
        "Dutch braid of 3 (ABOK 2966)",
        lambda: inverted_flat3(draw=False)[0],
        (
            ashley(2966),
            Link(
                "Animated Knots: three strand braid, the other way",
                "page",
                "https://www.animatedknots.com/three-strand-braid-knot-alt",
            ),
        ),
    ),
    "weave3": Entry(
        "Weave of 3 (ABOK 2973)", lambda: weave3(draw=False)[0], (ashley(2973),)
    ),
    "double_flat3": Entry(
        "Double flat sinnet of 3 (ABOK 2971)",
        lambda: double_flat3(draw=False)[0],
        (ashley(2971),),
    ),
    "square4": Entry(
        "Square sinnet of 4 (ABOK 2999)",
        lambda: square4(draw=False)[0],
        (
            ashley(2999),
            Link(
                "Animated Knots: four strand square sinnet",
                "page",
                "https://www.animatedknots.com/four-strand-square-sinnet-knot",
            ),
        ),
    ),
    "asymmetric_flat4": Entry(
        "Asymmetric flat sinnet of 4 (ABOK 2969)",
        lambda: asymmetric_flat4(draw=False)[0],
        (
            ashley(2969),
            Link(
                "A flat braid of 4, made",
                "video",
                "https://www.youtube.com/watch?v=7lTFIzm9BLY",
            ),
        ),
    ),
    "abok_2974": Entry(
        "Four-strand sinnet (ABOK 2974)",
        lambda: abok_2974(draw=False)[0],
        (
            ashley(2974),
            Link(
                "Animated Knots: four strand sinnet",
                "page",
                "https://www.animatedknots.com/four-strand-sinnet-knot-2974",
            ),
        ),
    ),
    "flat5": Entry(
        "Flat braid of 5",
        lambda: flat5(draw=False)[0],
        (
            Link(
                "A flat braid of 5, made",
                "video",
                "https://www.youtube.com/watch?v=uRy4wvJwSWA",
            ),
        ),
    ),
    "flat_sinnet5": Entry(
        "Flat sinnet of 5 (ABOK 2967)",
        lambda: flat_sinnet5(draw=False)[0],
        (ashley(2967),),
    ),
    "flat6": Entry(
        "Flat braid of 6",
        lambda: flat6(draw=False)[0],
        (
            Link(
                "A flat braid of 6, made",
                "video",
                "https://www.youtube.com/watch?v=ZHWlYBxL-mA",
            ),
        ),
    ),
    "regular_flat6": Entry(
        "Regular flat braid of 6",
        lambda: regular_flat6(draw=False)[0],
        (
            Link(
                "A regular flat braid of 6, made",
                "video",
                "https://www.youtube.com/watch?v=J65kCzm_BtI",
            ),
        ),
    ),
    "flat_sinnet7": Entry(
        "Flat sinnet of 7 (ABOK 2968)",
        lambda: flat_sinnet7(draw=False)[0],
        (ashley(2968),),
    ),
    "rectangular14": Entry(
        "Rectangular braid of 14", lambda: rectangular14(draw=False)[0]
    ),
    "rectangular20": Entry(
        "Rectangular braid of 20", lambda: rectangular20(draw=False)[0]
    ),
}
# Ashley's plats, each as its number names it.
CATALOG.update(
    {
        f"abok_{number}": Entry(
            f"ABOK #{number}, {plat.n_strands}-strand {plat.shape}",
            plat.braid,
            (ashley(number),),
        )
        for number, plat in ASHLEY_PLATS.items()
    }
)


# An example shows at least so many crossings.
_FEWEST_CROSSINGS = 12


def word_examples() -> list[dict[str, Any]]:
    """Braids to try as braid words, as plain data: each of
    :data:`CATALOG` reduced to the word it repeats, then
    :data:`WORD_EXAMPLES`.  A braid is repeated as many times as brings
    every strand home, twice or more: at least :data:`_FEWEST_CROSSINGS`
    crossings.

    Returns:
        Per braid, its ``word``, ``n_strands``, ``repeat`` and ``title``; a
        ring word's ``layout`` too.
    """
    from braidpy.pure_braid import closing_repeats, repeating_unit

    examples: list[dict[str, Any]] = []
    for entry in CATALOG.values():
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


# The catalogue's name as 0.3.0 shipped it, kept working.
from braidpy._renamed import renamed_globals

__getattr__ = renamed_globals(__name__, {"CATALOGUE": "CATALOG"})
