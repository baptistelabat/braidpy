# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The braid word a machine and its loading make.

The word is read from the machine's own motion.  Where a second, independent
reading exists — off the shape those carriers lay down — the two are compared,
because a mechanism and the braid it produces ought to say the same thing.
"""

import math

import pytest

from braidpy.braid import Braid
from braidpy.horn_gear import examples as ex
from braidpy.horn_gear.tracks import simulation_period
from braidpy.horn_gear.word import (
    annular_word,
    deck_center,
    flat_word,
    strands_for_checking,
)
from braidpy.symmetric_braid import braid_word

# ── A flat braider, read two ways ─────────────────────────────────────────────


@pytest.mark.parametrize("name, at_start", [("flat_braid_3", 0), ("flat_braid_4", 1)])
def test_the_mechanism_and_the_shape_give_the_same_braid(name, at_start):
    """The strongest check available: two derivations that share no code.

    One follows the carriers round the gears; the other reads crossings off
    the yarn hanging in space.  Neither is the other's implementation.  The
    square braid's two carriers cross just as the period starts: the yarn
    cut there, level, leaves that crossing out, which the mechanism counts
    first (``at_start``).
    """
    machine = getattr(ex, name)()
    period = simulation_period(machine)
    from_mechanism = flat_word(machine)
    from_shape = braid_word(
        strands_for_checking(machine, n_cycles=1, n_steps=period), n_samples=20000
    )
    n = len(machine.default_carriers())
    assert Braid(tuple(from_mechanism), n) == Braid(
        tuple(from_mechanism[:at_start] + from_shape), n
    )


def test_the_three_strand_flat_braid_is_the_braid_everybody_plaits():
    """σ₁⁻¹ σ₂ repeated — the braid you put in hair."""
    assert flat_word(ex.flat_braid_3()) == [-1, 2, -1, 2, -1, 2]


def test_a_word_only_uses_generators_the_strand_count_allows():
    machine = ex.flat_braid_9()
    word = flat_word(machine)
    carriers = len(machine.default_carriers())
    assert word, "a braider that makes no crossings is not braiding"
    assert all(1 <= abs(gen) <= carriers - 1 for gen in word)


# ── A tubular braider, read round its axis ────────────────────────────────────


@pytest.mark.parametrize(
    "name,strands", [("tubular_braid_8", 8), ("tubular_braid_12", 12)]
)
def test_half_the_carriers_wind_each_way_exactly_once(name, strands):
    """One period takes every carrier once round, half of them each way.

    That is what makes the braid balanced: the net rotation is nil, so the
    tube does not corkscrew.
    """
    word = annular_word(getattr(ex, name)())
    assert word.n_strands == strands
    windings = sorted(word.winding.values())
    assert windings[: strands // 2] == pytest.approx([-1.0] * (strands // 2))
    assert windings[strands // 2 :] == pytest.approx([1.0] * (strands // 2))
    assert word.net_winding == pytest.approx(0.0)


@pytest.mark.parametrize(
    "name,strands", [("tubular_braid_8", 8), ("tubular_braid_12", 12)]
)
def test_every_counter_rotating_pair_crosses_twice_a_period(name, strands):
    """Each of the n/2 carriers meets each of the n/2 going the other way.

    They separate by two full turns relative to one another over a period, so
    they cross twice: n²/2 crossings in all, which is a count the word can be
    held to without knowing anything about the machine's geometry.
    """
    word = annular_word(getattr(ex, name)())
    assert len(word.generators) == strands * strands // 2


def test_the_wrapping_pair_gets_the_last_index():
    """Index n is the pair whose numbering wraps, as in annulus_braid.

    A flat word has no room for it; an annular one must use it, or the strands
    either side of the seam could never be seen to cross.
    """
    word = annular_word(ex.tubular_braid_8())
    assert all(1 <= abs(gen) <= word.n_strands for gen in word.generators)
    assert any(abs(gen) == word.n_strands for gen in word.generators), (
        "no crossing of the wrapping pair: the ring is being read as a line"
    )


def test_the_word_depends_on_where_you_look_from():
    """A braid word is a property of a projection, not of a braid alone.

    Moving the point the braid is read around changes which strands count as
    neighbours, so it changes the word.  This is the thing most likely to
    surprise someone reading a word out of this module.
    """
    machine = ex.tubular_braid_8()
    axis = deck_center(machine)
    from_axis = annular_word(machine, around=axis)
    off_axis = annular_word(machine, around=(axis[0] + 4.0, axis[1]))
    assert from_axis.generators != off_axis.generators


def test_a_tube_read_flat_is_not_the_same_braid_as_a_tube_read_round():
    """Ordering a ring left to right is meaningless, and the word shows it.

    Kept as a test because it is the reason annular_word exists.
    """
    machine = ex.tubular_braid_8()
    flat = flat_word(machine)
    annular = annular_word(machine)
    assert len(flat) != len(annular.generators)


# ── What it refuses to do ─────────────────────────────────────────────────────


def test_a_machine_with_axials_counts_each_as_a_strand():
    """Carriers braid around an axial, so it belongs in the word: a strand
    standing still where it rises through the deck, after the carriers.
    Read so, soutache's two cords are in its word, and the mechanism and the
    yarns hanging in space, cords and all, give the same braid."""
    machine = ex.soutache_braid()
    period = simulation_period(machine)
    from_mechanism = flat_word(machine)
    strands = strands_for_checking(machine, n_cycles=1, n_steps=period, axials=True)
    assert len(strands) == len(machine.default_carriers()) + len(machine.axials)
    from_shape = braid_word(strands, n_samples=20000)
    n = len(strands)
    assert Braid(tuple(from_mechanism), n) == Braid(tuple(from_shape), n)
    assert max(abs(g) for g in from_mechanism) == len(strands) - 1


def test_a_ring_with_axials_counts_each_in_its_word_round_the_ring():
    machine = ex.triaxial_braid_16()
    word = annular_word(machine)
    assert word.n_strands == len(machine.default_carriers()) + len(machine.axials)
    # An axial stands still: it winds round the centre not at all.
    for k in range(len(machine.default_carriers()), word.n_strands):
        assert word.winding[k] == 0


# ── The loading is part of the question ───────────────────────────────────────


def test_a_different_loading_makes_a_different_braid():
    """The word belongs to the machine *and* its threading.

    Take a carrier off and the braid changes: the yarns that would have
    crossed it no longer do.
    """
    machine = ex.flat_braid_4()
    full = machine.default_carriers()
    assert len(full) > 2
    fewer = {cid: pos for cid, pos in list(full.items())[:-1]}
    assert flat_word(machine, carriers=full) != flat_word(machine, carriers=fewer)


def test_reading_more_steps_repeats_the_word():
    """A machine returns to its state after a period, so the braid repeats."""
    machine = ex.flat_braid_3()
    period = simulation_period(machine)
    once = flat_word(machine, n_steps=period)
    twice = flat_word(machine, n_steps=2 * period)
    assert twice == once + once


def test_the_center_defaults_to_the_axis_of_the_tube():
    """For a ring of gears the centroid is the hole they braid around."""
    machine = ex.tubular_braid_8()
    center = deck_center(machine)
    word = annular_word(machine)
    assert word.center == pytest.approx(center)
    assert math.hypot(*center) == pytest.approx(math.hypot(*word.center))


@pytest.mark.parametrize("name", ["soutache_braid", "princess_braid", "flat_braid_9"])
def test_a_carrier_passing_two_others_at_once_is_followed(name):
    """A carrier going left past two others within one sample: one pass of
    the neighbours exchanged one of them only, and the word's order of the
    strands was wrong from there on.  Read over the loading's period, every
    carrier back where it started, the word is a pure braid, and the same
    braid sampled four times as finely."""
    from braidpy.pure_braid import cycles

    machine = getattr(ex, name)()
    n_strands = len(machine.default_carriers()) + len(machine.axials)
    word = Braid(tuple(flat_word(machine)), n_strands)
    finer = Braid(tuple(flat_word(machine, n_substeps=256)), n_strands)
    assert all(len(cycle) == 1 for cycle in cycles(word))
    assert word == finer


def test_carriers_crossing_as_the_period_starts_are_counted_once():
    """Two carriers of the square braid's second gear, opposite each other,
    cross just as the machine starts and draw level again as it ends: the
    word counted that crossing neither at the start nor at the end, one
    period's word was eleven crossings and seemed to swap two strands.  It
    is twelve, a pure braid, and two periods' twice that."""
    from braidpy.pure_braid import cycles

    machine = ex.flat_braid_4()
    period = 8
    once = flat_word(machine, n_steps=period)
    twice = flat_word(machine, n_steps=2 * period)
    assert len(once) == 12
    assert len(twice) == 2 * len(once)
    assert all(len(cycle) == 1 for cycle in cycles(Braid(tuple(once), 4)))


# ── Round an axis, as moves round a ring ──────────────────────────────────────


def _round_a_core(machine, axis):
    """The machine's braid with a yarn fed at ``axis``, read flat: the
    reading :func:`ring_word` is checked against."""
    others = [a for a in machine.axials if a.anchor != axis.anchor]
    return flat_word(machine.with_axials(others + [axis]))


@pytest.mark.parametrize(
    "name, spot",
    [
        ("tubular_braid_8", -1),  # round the tube's hole
        ("tubular_braid_8", 0),  # round a gear of it
        ("princess_braid", 1),  # round its own axial, carriers in line with it
        ("flat_braid_3", 0),
        ("soutache_braid", 1),
    ],
)
def test_the_ring_word_is_the_braid_round_a_core_fed_there(name, spot):
    """Read round an axis, its core kept as a strand, the ring word is the
    braid the machine makes round a yarn fed there; the core taken away, the
    braid it makes with nothing there."""
    from braidpy.horn_gear.layout import axial_spots
    from braidpy.horn_gear.word import ring_word
    from braidpy.ring_program import same_braid

    machine = getattr(ex, name)()
    axis = axial_spots(machine)[spot]
    word = ring_word(machine, axis)
    n = word.n_strands
    assert same_braid(word.cored(), Braid(_round_a_core(machine, axis), n + 1))
    others = [a for a in machine.axials if a.anchor != axis.anchor]
    assert same_braid(word.braid(), Braid(flat_word(machine.with_axials(others)), n))


def test_the_default_axis_is_the_core_a_machine_braids_round():
    """A tube's hole; the axial a machine feeds; else a gear near the
    middle."""
    from braidpy.horn_gear.word import default_axis

    assert len(default_axis(ex.tubular_braid_8()).anchor) == 4
    assert default_axis(ex.princess_braid()).anchor == ("B",)
    assert len(default_axis(ex.flat_braid_3()).anchor) == 1


def test_a_tube_read_round_its_hole_goes_round_it_and_shortens():
    """Every strand of a tube goes once round its hole a period, half each
    way, so nothing is left of the turns once moved to the end: the
    shortened word is the n²/2 crossings, the same braid round the core."""
    from braidpy.horn_gear.word import ring_word

    word = ring_word(ex.tubular_braid_8())
    shorter = word.shortened()
    assert len(shorter.moves) == 8 * 8 // 2 < len(word.moves)
    assert all(abs(move) <= 8 for move in shorter.moves)
    assert shorter.cored() == word.cored()


def test_a_lace_card_of_a_tube_is_not_a_tube():
    """The lace card keeps its strands off the ring's seam: made from a
    tube's braid it makes the same braid, but a flat one curled up, not the
    tube round its core."""
    from braidpy.horn_gear.word import ring_word
    from braidpy.machine_catalog import LACE
    from braidpy.making.lace import lace_card
    from braidpy.ring_program import same_braid

    tube = ring_word(LACE["lace_tubular_8"].make().machine())
    card = lace_card(tube.braid())
    made = ring_word(card.machine(), carriers=card.threading())
    assert same_braid(made.braid(), tube.braid())
    assert not same_braid(made.cored(), tube.cored())


@pytest.mark.parametrize(
    "name, per_cycle", [("tubular_braid_16", 8), ("tubular_braid_8", 2)]
)
def test_a_tube_comes_round_long_before_its_cycle(name, per_cycle):
    """The shortest stretch that, made over and over, makes the cycle: its
    braid round the core repeated is the cycle's."""
    from braidpy.annulus_braid import cored_word
    from braidpy.horn_gear.word import ring_unit, ring_word
    from braidpy.ring_program import same_braid

    machine = getattr(ex, name)()
    unit, times = ring_unit(machine)
    assert times == per_cycle
    n = unit.n_strands
    repeated = Braid(tuple(cored_word(list(unit.moves) * times, n)), n + 1)
    assert same_braid(repeated, ring_word(machine).cored())
