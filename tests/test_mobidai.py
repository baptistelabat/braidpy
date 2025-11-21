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
    m.step()

    assert m.slots[1] is None
    assert m.slots[5].color == "red"


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
        m.step()


def test_rotation():
    """Rotation should shift each strand by the given number of slots."""
    config = MobidaiConfig(
        n_slots=8,
        strands=[Strand("red", 1), Strand("blue", 4)],
        moves=[],
        n_shift_after_cycle=2,
    )
    m = Mobidai(config)
    m.step()  # no moves, only rotation

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

    m.step()
    assert m.slots[3].color == "red"

    m.step()
    assert m.slots[5].color == "red"


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
