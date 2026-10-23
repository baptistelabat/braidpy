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

from braidpy.horn_gear import examples as ex
from braidpy.horn_gear.tracks import simulation_period
from braidpy.horn_gear.word import (
    annular_word,
    deck_centre,
    flat_word,
    strands_for_checking,
)
from braidpy.symmetric_braid import braid_word

# ── A flat braider, read two ways ─────────────────────────────────────────────


@pytest.mark.parametrize("name", ["flat_braid_3", "flat_braid_4"])
def test_the_mechanism_and_the_shape_give_the_same_word(name):
    """The strongest check available: two derivations that share no code.

    One follows the carriers round the gears; the other reads crossings off
    the yarn hanging in space.  Neither is the other's implementation.
    """
    machine = getattr(ex, name)()
    period = simulation_period(machine)
    from_mechanism = flat_word(machine)
    from_shape = braid_word(
        strands_for_checking(machine, n_cycles=1, n_steps=period), n_samples=20000
    )
    assert from_mechanism == from_shape


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
    axis = deck_centre(machine)
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


@pytest.mark.parametrize("name", ["princess_braid", "soutache_braid"])
def test_a_machine_with_axials_is_refused_rather_than_answered_wrongly(name):
    """Carriers braid around an axial, so it belongs in the word.

    Carrier trajectories do not include axials, so a word read from them would
    silently be missing strands.  Better to refuse.
    """
    machine = getattr(ex, name)()
    with pytest.raises(NotImplementedError, match="axial"):
        flat_word(machine)
    with pytest.raises(NotImplementedError, match="axial"):
        annular_word(machine)


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


def test_the_centre_defaults_to_the_axis_of_the_tube():
    """For a ring of gears the centroid is the hole they braid around."""
    machine = ex.tubular_braid_8()
    centre = deck_centre(machine)
    word = annular_word(machine)
    assert word.centre == pytest.approx(centre)
    assert math.hypot(*centre) == pytest.approx(math.hypot(*word.centre))
