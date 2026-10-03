# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Laying, drawing in and tightening a braid from any source of strands."""

import re
from types import SimpleNamespace

import matplotlib
import numpy as np
import pytest

from braidpy import Braid
from braidpy.kumihimo import Kumihimo
from braidpy.mobidai import Mobidai, MobidaiConfig, Move, Strand
from braidpy.parametric_braid import ParametricBraid
from braidpy.symmetric_braid import braid_word
from braidpy.take_off import (
    StrandTrajectories,
    braid_word_trajectories,
    default_take_off,
    disk_trajectories,
    kumihimo_steps,
    kumihimo_trajectories,
    lay_yarns,
    mobidai_steps,
    mobidai_trajectories,
    parametric_trajectories,
    tighten_yarns,
    visualize_yarns,
)


class _Curve:
    """A sampled curve, in the form :func:`braid_word` reads."""

    def __init__(self, s, x, y):
        self.s, self.x, self.y, self.length = s, x, y, float(s[-1])

    def position(self, z):
        return (np.interp(z, self.s, self.x), np.interp(z, self.s, self.y), z)


def _word_of_yarns(paths):
    """The word the laid yarns make, read down from the oldest end."""
    curves = []
    for pts in paths.points.values():
        braid = pts[: paths.formed_count]
        curves.append(_Curve(braid[0, 2] - braid[:, 2], braid[:, 0], braid[:, 1]))
    return braid_word(curves, n_samples=4000)


def _word_of_disk(trajectories, n_slots, clockwise=True):
    """The word strands on a disk make, read in slot order, inside as over."""
    turn = 1 if clockwise else -1
    curves = []
    for xy in trajectories.xy.values():
        angle = np.unwrap(np.arctan2(turn * xy[:, 0], xy[:, 1]))
        # Measured from slot 1, so the seam the reading starts at is there.
        angle += 2 * np.pi * (angle[0] < -1e-9)
        slot = angle * n_slots / (2 * np.pi) + 1
        inward = -np.hypot(xy[:, 0], xy[:, 1])
        curves.append(_Curve(trajectories.times, slot, inward))
    return braid_word(curves, n_samples=20000)


def _signed(words):
    """``"s1 s2^-1"`` and the like as signed generator indices."""
    return [
        -int(m[1]) if m[2] else int(m[1])
        for m in re.finditer(r"s(\d+)(\^-1)?", " ".join(words))
    ]


def _free_reduce(word):
    out = []
    for g in word:
        if out and out[-1] == -g:
            out.pop()
        else:
            out.append(g)
    return out


# ── Trajectories ──────────────────────────────────────────────────────────────


def test_trajectories_are_checked():
    with pytest.raises(ValueError, match="evenly spaced"):
        StrandTrajectories(np.array([0.0, 1.0, 3.0]), {0: np.zeros((3, 2))})
    with pytest.raises(ValueError, match="expected"):
        StrandTrajectories(np.array([0.0, 1.0]), {0: np.zeros((3, 2))})
    with pytest.raises(ValueError, match="two samples"):
        StrandTrajectories(np.array([0.0]), {0: np.zeros((1, 2))})


def test_default_take_off_is_the_mean_speed():
    times = np.linspace(0.0, 2.0, 5)
    moving = np.column_stack([np.linspace(0.0, 4.0, 5), np.zeros(5)])
    still = np.ones((5, 2))
    traj = StrandTrajectories(times, {0: moving, 1: still})
    assert default_take_off(traj) == pytest.approx((4.0 / 2.0) / 2)
    assert traj.centre() == pytest.approx(np.concatenate([moving, still]).mean(0))


def test_parametric_braid_is_read_as_it_is_drawn():
    strands = Braid([1, -2]).to_parametric_strands()
    traj = parametric_trajectories(ParametricBraid(strands), n_samples=11)
    assert traj.times == pytest.approx(np.linspace(0, 1, 11))
    for key, strand in enumerate(strands):
        assert traj.xy[key][4] == pytest.approx(strand.evaluate(0.4)[:2])


# ── A braid word, laid ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word",
    [[1, -2, 1, -2, 1, -2], [1, 1, 2, -1, -1, 2], [1, 2, 3, -1, -2, 2, 1]],
)
def test_braid_word_survives_laying_drawing_in_and_tightening(word):
    """The braid the word names is the braid that comes out, at every stage."""
    traj = braid_word_trajectories(word)
    assert _word_of_yarns(lay_yarns(traj)) == word

    jammed = lay_yarns(traj, yarn_diameter=0.4)
    assert jammed.closest_approach() == pytest.approx(0.4)
    assert _word_of_yarns(jammed) == word

    # Tightening may pull out a crossing that undoes itself, but never changes
    # the braid.
    tight, _ = tighten_yarns(jammed, 0.4, iterations=100)
    assert tight.closest_approach() >= 0.4 * (1 - 2e-3)
    assert _free_reduce(_word_of_yarns(tight)) == _free_reduce(word)


def test_braid_word_layout():
    traj = braid_word_trajectories(Braid([1]), spacing=2.0, lift=0.25)
    xs = sorted(xy[0, 0] for xy in traj.xy.values())
    assert xs == pytest.approx([0.0, 2.0])
    # Half way through the crossing the two are lifted to either side.
    middle = len(traj.times) // 4
    lifts = sorted(xy[middle, 1] for xy in traj.xy.values())
    assert lifts[0] == pytest.approx(-lifts[1])
    assert lifts[1] == pytest.approx(0.5, rel=0.05)


# ── A disk ────────────────────────────────────────────────────────────────────


def test_a_moving_strand_passes_over_on_the_inside():
    # Over, seen from above the disk, is inside.  Toward higher slots, over
    # the strand in between: a positive crossing, as the mobidai has it.
    traj = disk_trajectories({"a": 1, "b": 2}, [{"a": 2}], n_slots=8)
    assert _word_of_disk(traj, 8) == [1]
    radius = np.hypot(*traj.xy["a"].T)
    assert radius.min() == pytest.approx(0.85)
    assert radius[0] == radius[-1] == pytest.approx(1.0)
    # The other way, under it.
    back = disk_trajectories({"a": 3, "b": 2}, [{"a": -2}], n_slots=8)
    assert _word_of_disk(back, 8) == [-1]


def test_turning_the_disk_lifts_nothing():
    traj = disk_trajectories({0: 1, 1: 5}, [{0: 2, 1: 2}], n_slots=8)
    for xy in traj.xy.values():
        assert np.hypot(*xy.T) == pytest.approx(1.0)
    assert _word_of_disk(traj, 8) == []
    # Slot 1 at the top, and clockwise means clockwise seen from above.
    assert traj.xy[0][0] == pytest.approx([0.0, 1.0])
    assert traj.xy[0][-1] == pytest.approx([1.0, 0.0])
    mirrored = disk_trajectories({0: 1, 1: 5}, [{0: 2, 1: 2}], 8, clockwise=False)
    assert mirrored.xy[0][-1] == pytest.approx([-1.0, 0.0])


def test_disk_refuses_impossible_moves():
    with pytest.raises(ValueError, match="one slot"):
        disk_trajectories({0: 1, 1: 3}, [{0: 2}], n_slots=8)
    with pytest.raises(ValueError, match="unknown"):
        disk_trajectories({0: 1}, [{5: 1}], n_slots=8)
    with pytest.raises(ValueError, match="not on a slot"):
        disk_trajectories({0: 9}, [], n_slots=8)
    with pytest.raises(ValueError, match="same slot"):
        disk_trajectories({0: 1, 1: 1}, [], n_slots=8)


def _mobidai_config(moves, positions, n_slots=16, shift=0, clockwise=True):
    return MobidaiConfig(
        strands=[Strand("red", p) for p in positions],
        moves=[Move(a, b, f) for a, b, f in moves],
        n_shift_after_cycle=shift,
        n_slots=n_slots,
        is_clockwise=clockwise,
    )


def test_mobidai_steps_follow_its_rules():
    config = _mobidai_config(
        [(1, 4, 0), (12, 10, 0), (5, 7, 0), (2, 15, 0), (3, 6, -1)],
        positions=[1, 2, 3, 12],
        shift=1,
    )
    # Ids are only assigned by Mobidai itself; the config's are -1.
    start, steps = mobidai_steps(config, n_cycles=1)
    assert start == {0: 1, 1: 2, 2: 3, 3: 12}
    assert steps == [
        {0: 3},  # the short way, up
        {3: -2},  # the short way, down
        # slot 5 is empty: nothing moves
        {1: -3},  # 2 to 15 is shorter downward, through slot 1
        {2: -13},  # forced the long way round
        {0: 1, 1: 1, 2: 1, 3: 1},  # the disk turns
    ]
    # A Mobidai is read through its config, without being run.
    assert mobidai_steps(SimpleNamespace(config=config))[0] == start


@pytest.mark.parametrize(
    "positions, moves",
    [
        ([1, 2, 5, 6], [(1, 3), (6, 4)]),
        ([3, 4, 5, 9, 10], [(3, 7), (10, 8), (4, 2), (9, 11), (7, 6)]),
        ([5, 6, 7, 8], [(5, 10), (8, 3), (6, 9), (7, 11)]),
    ],
)
def test_mobidai_word_matches_the_laid_strands(positions, moves):
    """The crossings the strands make are the ones the mobidai writes down."""
    moves = [(a, b, 0) for a, b in moves]
    mobidai = Mobidai(_mobidai_config(moves, positions, n_slots=24))
    mobidai.all_steps()
    traj = mobidai_trajectories(_mobidai_config(moves, positions, 24), n_cycles=1)
    assert _word_of_disk(traj, 24) == _signed(mobidai.braid_word)


def test_numbering_the_disk_the_other_way_is_its_mirror_image():
    moves = [(1, 3, 0), (6, 4, 0)]
    forward = mobidai_trajectories(_mobidai_config(moves, [1, 2, 5, 6]), n_cycles=1)
    mirror = mobidai_trajectories(
        _mobidai_config(moves, [1, 2, 5, 6], clockwise=False), n_cycles=1
    )
    for key in forward.xy:
        assert mirror.xy[key][:, 0] == pytest.approx(-forward.xy[key][:, 0])
        assert mirror.xy[key][:, 1] == pytest.approx(forward.xy[key][:, 1])
    # Read in slot order, a mirror image read the mirrored way is unchanged.
    assert _word_of_disk(mirror, 16, clockwise=False) == _word_of_disk(forward, 16)


# ── Kumihimo ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("n_strands", [8, 12])
def test_kumihimo_swap_crosses_as_its_word_says(n_strands):
    matplotlib.use("Agg")
    kumihimo = Kumihimo(n_strands).move("S")
    traj = kumihimo_trajectories(kumihimo)
    assert _word_of_disk(traj, 2 * n_strands, clockwise=False) == list(
        kumihimo.braid_word
    )


def test_kumihimo_steps():
    n_slots, start, steps = kumihimo_steps("SR", n_strands=8)
    assert n_slots == 16
    assert start == {s: 2 * s + 1 for s in range(8)}
    assert steps[:3] == [{0: 9}, {4: -8}, {0: -1}]
    assert steps[3] == {s: -4 for s in range(8)}  # a quarter turn clockwise
    # Kumihimo's own record reads the same.
    assert kumihimo_steps(Kumihimo(8).move("SR"))[2] == steps
    with pytest.raises(ValueError, match="multiple of four"):
        kumihimo_steps("S", n_strands=6)
    with pytest.raises(ValueError, match="n_strands"):
        kumihimo_steps("S")


def test_kumihimo_is_drawn_where_kumihimo_draws_it():
    kumihimo = Kumihimo(8)
    traj = kumihimo_trajectories("R", n_strands=8)
    for strand in range(8):
        angle = kumihimo.angles[strand]
        assert traj.xy[strand][0] == pytest.approx([-np.sin(angle), np.cos(angle)])


def test_kumihimo_is_laid_and_tightened():
    traj = kumihimo_trajectories("SR" * 6, n_strands=8)
    paths = lay_yarns(traj, yarn_diameter=0.15, fell_radius=0.0)
    tight, history = tighten_yarns(paths, 0.15, iterations=40)
    assert history["length"][-1] < history["length"][0]
    assert tight.closest_approach(include_fell=False) >= 0.15 * (1 - 2e-3)


def test_mobidai_is_laid_and_tightened():
    config = _mobidai_config(
        [(1, 5, 0), (9, 13, 0), (6, 2, 0), (14, 10, 0)],
        positions=[1, 3, 6, 9, 11, 14],
        shift=2,
    )
    traj = mobidai_trajectories(config, n_cycles=3)
    assert set(traj.xy) == set(range(6))
    paths = lay_yarns(traj, yarn_diameter=0.15, fell_radius=0.0)
    tight, history = tighten_yarns(paths, 0.15, iterations=40)
    assert history["length"][-1] < history["length"][0]
    assert tight.closest_approach(include_fell=False) >= 0.15 * (1 - 2e-3)

    fig = visualize_yarns(tight)
    names = [t.name for t in fig.data]
    assert "Disk" in names and "Braiding point" in names
    assert sum(1 for n in names if n.startswith("Strand ")) == 6
    assert any(t.type == "surface" for t in fig.data)


def test_kongo_creeps_one_slot_a_cycle_and_comes_round():
    from braidpy.mobidai_catalog import KONGO_8

    # The drift is read off the cycle: no one has to say it.
    start, steps = mobidai_steps(KONGO_8.to_config(), n_cycles=32)
    assert len(steps) == 4 * 32  # no move ever finds its slot empty
    where = dict(start)
    for step in steps:
        for strand, delta in step.items():
            where[strand] = (where[strand] - 1 + delta) % 32 + 1
    assert where == start  # round the whole disk, back where it began
    # The second cycle opens with the book's next two moves, (32, 14) and
    # (16, 30): the strands that started there, sent fourteen slots round.
    second = [list(step.items())[0] for step in steps[4:6]]
    made = [(start[k], (start[k] - 1 + d) % 32 + 1) for k, d in second]
    assert made == [(32, 14), (16, 30)]
    # Said outright, no drift sends the second cycle's moves to empty slots.
    assert len(mobidai_steps(KONGO_8.to_config(), n_cycles=2, drift=0)[1]) == 4


def test_every_slot_is_named_where_it_is():
    traj = disk_trajectories({0: 1}, [{}], n_slots=8)
    assert [name for _, _, name in traj.slots] == [str(s) for s in range(1, 9)]
    assert traj.slots[0][:2] == pytest.approx((0.0, 1.0))  # slot 1 at the top
    assert traj.slots[2][:2] == pytest.approx((1.0, 0.0))  # clockwise
    # Kumihimo names its own positions, not the slots a swap passes through.
    kumi = kumihimo_trajectories("R", n_strands=8)
    assert [name for _, _, name in kumi.slots] == [str(p) for p in range(8)]


def test_slot_offset_turns_the_numbering():
    traj = disk_trajectories({0: 32, 1: 1}, [{}], n_slots=32, slot_offset=0.5)
    left, right = traj.xy[0][0], traj.xy[1][0]
    # The top mark between slot 32 and slot 1: the pair straddles it.
    assert left[0] == pytest.approx(-right[0])
    assert left[1] == pytest.approx(right[1])
    assert right[0] > 0


# ── A disk's braid, laid on a ring ────────────────────────────────────────────


def test_crossings_are_read_off_the_moves():
    from braidpy.take_off import disk_crossings

    # a moves from 1 to 5 over b and c; the disk turns, leaving a at 6, b at
    # 3 and c at 5; then c moves on to 7, over a.
    order, crossings = disk_crossings(
        {"a": 1, "b": 2, "c": 4}, [{"a": 4}, {"a": 1, "b": 1, "c": 1}, {"c": 2}], 8
    )
    assert order == ["a", "b", "c"]
    assert crossings == [("a", "b"), ("a", "c"), ("c", "a")]
    with pytest.raises(ValueError, match="several strands"):
        disk_crossings({"a": 1, "b": 3}, [{"a": 1, "b": -1}], 8)


@pytest.mark.parametrize(
    "positions, moves",
    [
        ([1, 2, 5, 6], [(1, 3), (6, 4)]),
        ([3, 4, 5, 9, 10], [(3, 7), (10, 8), (4, 2), (9, 11), (7, 6)]),
    ],
)
def test_the_ring_keeps_the_mobidai_word(positions, moves):
    """Read round the ring, inside as over, the strands make the mobidai's braid.

    The same braid, not necessarily the same spelling: crossings of
    different strands are made side by side on the ring, and two of them in
    one row may be read in either order.
    """
    from braidpy.take_off import disk_crossings, ring_trajectories

    moves = [(a, b, 0) for a, b in moves]
    mobidai = Mobidai(_mobidai_config(moves, positions, n_slots=24))
    mobidai.all_steps()
    start, steps = mobidai_steps(_mobidai_config(moves, positions, 24))
    order, crossings = disk_crossings(start, steps, 24)
    ring = ring_trajectories(order, crossings, diameter=0.2)
    n = len(order)
    assert Braid(tuple(_word_of_disk(ring, n)), n_strands=n) == Braid(
        tuple(_signed(mobidai.braid_word)), n_strands=n
    )


def test_crossings_are_timed_and_made_in_rows():
    from braidpy.take_off import crossing_rows, disk_crossing_steps, disk_crossings

    start = {"a": 1, "b": 2, "c": 4}
    steps = [{"a": 4}, {"a": 1, "b": 1, "c": 1}, {"c": 2}]
    order, crossings, made_at = disk_crossing_steps(start, steps, 8)
    assert (order, crossings) == disk_crossings(start, steps, 8)
    # a passes b a quarter of the way to slot 5, c three quarters; the turn
    # crosses nothing; c passes a half way to slot 7.
    assert made_at == [0.25, 0.75, 2.5]
    # Each crossing waits for its strands' previous one.
    assert crossing_rows(order, crossings) == [0, 1, 2]
    # Crossings of different strands share a row, even an earlier one...
    later = [("a", "b"), ("b", "a"), ("c", "d")]
    assert crossing_rows(list("abcd"), later) == [0, 1, 0]
    # ...unless the rows must come in the order the crossings are made.
    assert crossing_rows(list("abcd"), later, in_turn=True) == [0, 1, 1]


def test_ring_refuses_crossings_of_strangers():
    from braidpy.take_off import ring_trajectories

    with pytest.raises(ValueError, match="not neighbours"):
        ring_trajectories(["a", "b", "c", "d"], [("a", "c")])


def test_kongo_comes_out_round():
    from braidpy.mobidai_catalog import KONGO_8
    from braidpy.take_off import mobidai_braid

    d = 0.12
    braid = mobidai_braid(KONGO_8.to_config(), d, n_cycles=4, iterations=150)
    assert braid.closest_approach() >= d * (1 - 2e-3)
    formed = braid.formed()
    middle = formed[:, formed.shape[1] // 2, :2]
    middle = middle - middle.mean(axis=0)
    width, thickness = np.ptp(middle @ np.linalg.svd(middle)[2].T, axis=0)
    # Eight strands round a small core: a round cord about three yarns across,
    # not the flat two rows the disk's waiting places lay.
    assert width < 1.6 * thickness
    assert 2 * d < width < 5 * d


def test_kumihimo_braid():
    from braidpy.take_off import kumihimo_braid

    braid = kumihimo_braid("SR" * 4, 0.12, n_strands=8, iterations=60)
    assert len(braid.points) == 8
    assert braid.closest_approach() >= 0.12 * (1 - 2e-3)
