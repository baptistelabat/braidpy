import math

from braidpy.craft_design_online import (
    BraidModel,
    create_initial_braid_data,
    Step,
    Move,
)


def test_load_from_file():
    loaded_braid = BraidModel.load_from_file("tests/abok3054.b3d")

    assert loaded_braid.n_strands == 17
    assert type(loaded_braid.thread_states) is list
    assert type(loaded_braid.steps) is list


def test_create_initial_braid_data():
    initial_states = create_initial_braid_data(n_strands=5)
    assert len(initial_states) == 5


def test_step():
    main_step = Step(
        type=None,  # Example usage of the new Literal type
        tighten=0,
        rotate=math.pi / 36,  # Example rotation of 5 degrees
        repeat_from=1,
        repeat_times=5,  # Repeat the pattern 5 times
        moves=[],
    )

    assert main_step.type is None
    assert main_step.tighten == 0
    assert main_step.rotate == math.pi / 36
    assert main_step.repeat_from == 1
    assert main_step.repeat_times == 5
    assert main_step.moves == []


def test_braid_model():
    # Generate mock states first to determine thread count
    initial_states = create_initial_braid_data(n_strands=3)

    new_braid = BraidModel(
        n_strands=len(initial_states),  # MUST provide n_threads during initialization
        thread_states=initial_states,
    )
    new_braid.save_to_file(filepath="tests/3strands_no_step.json", encode=False)
    new_braid.save_to_file(filepath="tests/3strands_no_step.b3d", encode=True)

    # Create the single Step object containing configuration and moves
    move_step = Step(
        type="threadMove",  # Example usage of the new Literal type
        num=1,
        moves=[
            Move(from_val=0.0, to_val=3.14, id=0),
            Move(from_val=-2.0943951023931957 % (2 * math.pi), to_val=2.7, id=2),
        ],
    )
    new_braid.add_step(move_step)
    new_braid.save_to_file(filepath="tests/3strands_moves_step.json", encode=False)
    new_braid.save_to_file(filepath="tests/3strands_moves_step.b3d", encode=True)
    repeat_step = Step(
        type="repeat",  # Example usage of the new Literal type
        repeat_from=1,
        repeat_times=2,  # Repeat the pattern 5 times
        poss=[],
        moves=[],
    )

    new_braid.add_step(repeat_step)
    new_braid.save_to_file(filepath="tests/3strands_repeat_step.json", encode=False)
    new_braid.save_to_file(filepath="tests/3strands_repeat_step.b3d", encode=True)

    assert len(new_braid.steps) == 3


def test_save_to_file():
    loaded_braid = BraidModel.load_from_file("tests/abok3054.b3d")

    # Test saving to json
    loaded_braid.save_to_file(filepath="tests/abok3054_out.json", encode=False)

    # Check initial file is not modified when saving back
    loaded_braid.save_to_file(filepath="tests/abok3054.b3d", encode=True)


def test_get_main_config():
    loaded_braid = BraidModel.load_from_file("tests/abok3054.b3d")
    main_config = loaded_braid.get_main_config()
    assert main_config.type is None


def test_get_programmatic_code():
    loaded_braid = BraidModel.load_from_file("tests/abok3054.b3d")
    creation_code = loaded_braid.get_programmatic_code()
    assert type(creation_code) is str
