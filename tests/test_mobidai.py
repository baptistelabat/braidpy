import pytest
from braidpy.mobidai import Mobidai, MobidaiConfig, Strand, Move, SlotAlreadyInUseError


def test_initialization():
    """Mobidai should correctly place strands in slots."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("blue", 3)],
        moves=[],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)

    assert m.slots[1].color == "red"
    assert m.slots[3].color == "blue"
    assert m.slots[2] is None
    assert m.slots[4] is None


def test_step_simple_move():
    """A single move should relocate a strand."""
    config = MobidaiConfig(
        n_slots=8, strands=[Strand("red", 1)], moves=[Move(1, 5)], n_shift_after_cycle=0
    )
    m = Mobidai(config)
    m.all_steps()

    assert m.slots[1] is None
    assert m.slots[5].color == "red"
    assert m.braid_word == []


def test_step_simple_crossing():
    """A single move should relocate a strand."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("red", 2)],
        moves=[Move(1, 5)],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)
    m.all_steps()

    assert m.slots[1] is None
    assert m.slots[5].color == "red"
    assert m.braid_word == ["s1"]


def test_step_multiple_crossings():
    """A single move should relocate a strand."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("red", 2), Strand("red", 4)],
        moves=[Move(1, 5)],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)
    m.all_steps()

    assert m.slots[1] is None
    assert m.slots[5].color == "red"
    assert m.braid_word == ["s1 s2"]


def test_step_simple_back_crossing():
    """A single move should relocate a strand."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 3), Strand("red", 2)],
        moves=[Move(3, 1)],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)
    m.all_steps()

    assert m.slots[3] is None
    assert m.slots[1].color == "red"
    assert m.braid_word == ["s1^-1"]


def test_step_multiple_back_crossings():
    """A single move should relocate a strand."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 2), Strand("red", 3), Strand("red", 4)],
        moves=[Move(4, 1)],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)
    m.all_steps()

    assert m.slots[4] is None
    assert m.slots[1].color == "red"
    assert m.braid_word == ["s2^-1 s1^-1"]


def test_step_conflict_raises():
    """Moving into an occupied slot must raise an error."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("blue", 5)],
        moves=[Move(1, 5)],  # target slot already occupied
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)

    with pytest.raises(SlotAlreadyInUseError):
        m.all_steps()


def test_rotation():
    """Rotation should shift each strand by the given number of slots."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("blue", 4)],
        moves=[],
        n_shift_after_cycle=2,
    )
    m = Mobidai(config)
    m.all_steps()  # no moves, only rotation

    assert m.slots[3].color == "red"
    assert m.slots[6].color == "blue"


def test_multiple_steps():
    """Simulating multiple steps should apply moves repeatedly."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1)],
        moves=[Move(1, 3), Move(3, 5)],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)

    m.all_steps()
    assert m.slots[5].color == "red"
    assert m.braid_word == []


def test_multiple_steps_and_shift():
    """Simulating multiple steps should apply moves repeatedly."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1)],
        moves=[Move(1, 3), Move(3, 5)],
        n_shift_after_cycle=2,
    )
    m = Mobidai(config)

    m.all_steps()
    assert m.slots[7].color == "red"
    assert m.braid_word == []


def test_visualization_runs():
    """Visualization should run without raising exceptions."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 3)],
        moves=[],
        n_shift_after_cycle=0,
    )
    m = Mobidai(config)

    # We do NOT show the plot, just ensure it executes
    m.visualize()  # must not raise
