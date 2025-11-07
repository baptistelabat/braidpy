import json
import os
import math
from typing import List, Optional, Literal
import urllib.parse
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, DataClassJsonMixin, config


# --- Dataclass Definitions for the Braid Structure ---


@dataclass_json
@dataclass(frozen=True)
class Point(DataClassJsonMixin):
    """Represents a single 3D point (x, y, z) in a thread's path."""

    x: float
    y: float
    z: float


@dataclass_json
@dataclass(frozen=True)
class Move(DataClassJsonMixin):
    """
    Represents a single crossover step in the braid pattern.
    Maps 'from_val' to 'from' and 'to_val' to 'to'.
    """

    from_val: float = field(metadata=config(field_name="from"))
    to_val: float = field(metadata=config(field_name="to"))
    id: Optional[int] = None


@dataclass_json
@dataclass(frozen=True)
class AnglePosition(DataClassJsonMixin):
    """ """

    angle: float
    id: str


@dataclass_json
@dataclass
class ThreadState(DataClassJsonMixin):
    """
    The state of a single thread.
    Maps Python names (color, dir_val) to JSON names (colour, dir).
    """

    color: int = field(metadata=config(field_name="colour"))
    dir_val: float = field(metadata=config(field_name="dir"))
    poss: List[Point] = field(default_factory=list)  # Initial 3D path points


@dataclass_json
@dataclass(frozen=True)
class Step(DataClassJsonMixin):
    """
    Represents a block of moves and the configuration parameters associated with that block.
    This assumes a file structure where configuration is nested under a 'steps' list.
    """

    # NOTE: Updated to include "Repeat" as per user request
    type: Optional[None | Literal["threadMove", "repeat"]] = None
    num: Optional[int] = None
    moves: List[Move] = field(default_factory=list)

    # Configuration parameters, previously top-level, now nested here
    tighten: Optional[int] = 0
    rotate: Optional[float] = 0.0
    repeat_from: Optional[int] = field(
        default=1, metadata=config(field_name="repeatFrom")
    )
    repeat_times: Optional[int] = field(
        default=1, metadata=config(field_name="repeatTimes")
    )
    poss: Optional[list[AnglePosition]] = field(default_factory=list)


@dataclass_json
@dataclass
class BraidModel(DataClassJsonMixin):
    """
    Represents the complete 3D braid structure and configuration.
    The configuration parameters (tighten, rotate, repeat_from, repeat_times)
    are now assumed to be within the first element of the 'steps' list.
    """

    n_threads: int = field(metadata=config(field_name="nThreads"))

    # Nested lists of dataclasses
    thread_states: List[ThreadState] = field(
        metadata=config(field_name="threadStates"), default_factory=list
    )
    # The 'steps' list, which contains all move blocks and config info
    steps: List[Step] = field(metadata=config(field_name="steps"), default_factory=list)

    def get_main_config(self) -> Step:
        """Returns the configuration from the first (and assumed only) Step element."""
        if not self.steps:
            # Return a default step if the list is empty to prevent errors
            return Step()
        return self.steps[0]

    def __str__(self) -> str:
        """
        Provides a human-readable summary representation of the braid model.
        Uses the parameters from the main step configuration.
        """
        main_config = self.get_main_config()
        steps_count = len(main_config.moves)
        steps_summary = (
            f"[{main_config.moves[0]!r}, ... ({steps_count - 1} more moves)]"
            if steps_count > 1
            else str(main_config.moves)
        )

        return (
            f"BraidModel(\n"
            f"  Threads: {self.n_threads},\n"
            f"  Repeat: {main_config.repeat_times} times (starting from move {main_config.repeat_from}),\n"
            f"  Rotation: {main_config.rotate:.4f} rad,\n"
            f"  Tightness: {main_config.tighten},\n"
            f"  Moves in Pattern ({steps_count}): {steps_summary}\n"
            f")"
        )

    def save_to_file(self, filepath: str):
        """
        Saves the BraidModel configuration to a URL-encoded JSON file using dataclasses-json.
        """
        try:
            # Use dataclasses_json to get the JSON string, ensuring field names are correct
            json_data = self.to_json(indent=4)

            # URL-encode the JSON string before writing
            encoded_data = urllib.parse.quote(json_data)

            with open(filepath, "w") as f:
                f.write(encoded_data)
            print(f"Braid model successfully saved to URL-encoded file: {filepath}")
        except Exception as e:
            print(f"Error saving file: {e}")

    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["BraidModel"]:
        """
        Loads a BraidModel configuration from a URL-encoded JSON file using dataclasses-json.
        """
        try:
            # 1. Read the raw, potentially URL-encoded content
            with open(filepath, "r") as f:
                raw_content = f.read()

            # 2. URL-decode the content
            decoded_content = urllib.parse.unquote(raw_content)

            # --- CRITICAL: Manually parse and restructure the flat JSON to fit the Step class ---
            data = json.loads(decoded_content)

            # 3. Load the BraidModel from the restructured dict
            model = cls.from_dict(data)

            print(f"Braid model successfully loaded and decoded from: {filepath}")
            return model
        except FileNotFoundError:
            print(f"Error: File not found at {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file after URL-decoding: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during loading: {e}")
            return None

    def get_programmatic_code(self) -> str:
        """
        Generates Python code to programmatically recreate the model instance.
        """
        main_config = self.get_main_config()

        code = []
        code.append("# --- Programmatic Braid Model Creation Code ---")
        code.append(
            "from your_module import BraidModel, ThreadState, Move, Point, Step"
        )
        code.append("import math")

        # 1. Instantiate the Model
        code.append("\n# 1. Initialize the Braid Model")
        code.append("recreated_braid = BraidModel(")
        code.append(f"    n_threads={self.n_threads},")  # Initial thread count
        code.append("    thread_states=[")
        # Thread states are too complex/long to print, so we'll call the external mock function
        code.append(f"        *create_initial_braid_data(num_threads={self.n_threads})")
        code.append("    ],")
        code.append("    steps=[")
        code.append("        Step(")
        code.append(f"            tighten={main_config.tighten},")
        code.append(f"            rotate={main_config.rotate},")
        code.append(f"            repeat_from={main_config.repeat_from},")
        code.append(f"            repeat_times={main_config.repeat_times},")
        code.append("            moves=[")
        for move in main_config.moves:
            code.append(
                f"                Move(from_val={move.from_val}, to_val={move.to_val}),"
            )
        code.append("            ]")
        code.append("        )")
        code.append("    ]")
        code.append(")")

        code.append("\n# 2. Print Verification")
        code.append("print('Braid Model Recreated Successfully:')")
        code.append("print(recreated_braid)")

        return "\n".join(code)


# --- Helper Function for Demonstration (Now returns ThreadState objects) ---


def create_initial_braid_data(num_threads: int = 5) -> List[ThreadState]:
    """Creates mock initial data for demonstration, returning ThreadState dataclasses."""
    states: List[ThreadState] = []
    base_color = 0xAAAAAA

    for i in range(num_threads):
        angle = (2 * math.pi / num_threads) * i
        radius = 5.0
        initial_points = [
            Point(x=radius * math.cos(angle), y=radius * math.sin(angle), z=0.0),
            Point(x=radius * math.cos(angle), y=radius * math.sin(angle), z=1.0),
            Point(
                x=radius * math.cos(angle) * 0.9,
                y=radius * math.sin(angle) * 0.9,
                z=2.0,
            ),
        ]

        states.append(
            ThreadState(
                color=base_color + (i * 100000),
                dir_val=0.1 + (i * 0.05),
                poss=initial_points,
            )
        )
    return states


if __name__ == "__main__":
    OUTPUT_FILE = "new_braid_config.json"

    # 1. CREATE A NEW BRAID MODEL (Simulating the core structure)
    print("--- 1. Creating a New Braid Model ---")

    # Generate mock states first to determine thread count
    initial_states = create_initial_braid_data(num_threads=5)

    # Create the single Step object containing configuration and moves
    main_step = Step(
        type="None",  # Example usage of the new Literal type
        tighten=0,
        rotate=math.pi / 36,  # Example rotation of 5 degrees
        repeat_from=1,
        repeat_times=5,  # Repeat the pattern 5 times
        moves=[],
    )

    # Create the single Step object containing configuration and moves
    step = Step(
        type="threadMove",  # Example usage of the new Literal type
        tighten=0,
        rotate=math.pi / 36,  # Example rotation of 5 degrees
        repeat_from=1,
        repeat_times=5,  # Repeat the pattern 5 times
        poss=[],
        moves=[
            Move(from_val=0.5, to_val=0.6),
            Move(from_val=1.2, to_val=1.0),
            Move(from_val=0.785, to_val=0.785),
            Move(from_val=2.356, to_val=2.4),
        ],
    )

    new_braid = BraidModel(
        n_threads=len(initial_states),  # MUST provide n_threads during initialization
        thread_states=initial_states,
        steps=[main_step],
    )

    # 2. WRITE TO FILE
    print(
        f"\n--- 2. Saving Model to {OUTPUT_FILE} (Will be in the new, nested format) ---"
    )
    new_braid.save_to_file(OUTPUT_FILE)

    # 3. LOAD FROM FILE (Simulating loading the ORIGINAL, flat file format)
    # Since we can't truly load the original file in this environment,
    # we simulate the structure of the *original* file by creating a temporary, flat dict
    # that 'load_from_file' is designed to restructure.
    print("\n--- 3. Simulating Loading the Original, FLAT File Format ---")

    # This dictionary represents the FLAT structure that 'load_from_file' expects to DECODE
    flat_data_mock = {
        "nThreads": 7,
        "threadStates": create_initial_braid_data(
            num_threads=7
        ).to_dict(),  # 7 threads for a change
        "tighten": 1,
        "rotate": 0.05,
        "repeatFrom": 2,
        "repeatTimes": 8,
        "moves": [
            {"from": 0.1, "to": 0.2},
            {"from": 1.9, "to": 1.8},
        ],
    }

    # Save the flat structure mock (URL-encoded) to a temporary file
    TEMP_FLAT_FILE = "temp_flat_mock.json"
    encoded_flat_data = urllib.parse.quote(json.dumps(flat_data_mock, indent=4))
    with open(TEMP_FLAT_FILE, "w") as f:
        f.write(encoded_flat_data)

    # Load the mock file, which triggers the manual restructuring logic
    loaded_braid = BraidModel.load_from_file(TEMP_FLAT_FILE)

    # Clean up mock file
    if os.path.exists(TEMP_FLAT_FILE):
        os.remove(TEMP_FLAT_FILE)

    # 4. Verification
    if loaded_braid:
        main_config = loaded_braid.get_main_config()
        print("\n--- 4. Verification of Loaded and Restructured Data ---")
        print("--- String Representation (__str__) ---")
        print(loaded_braid)

        print("\n--- Programmatic Re-creation Code ---")
        creation_code = loaded_braid.get_programmatic_code()
        print(creation_code)

        # Verification checks
        print(f"\nLoaded Threads: {loaded_braid.n_threads}")
        print(f"Loaded Steps Count: {len(main_config.moves)}")
        print(
            f"First Step (from, to): {main_config.moves[0].from_val:.3f}, {main_config.moves[0].to_val:.3f}"
        )
        print(
            f"Repetition Info: Repeats from index {main_config.repeat_from} for {main_config.repeat_times} times."
        )
        print(f"Tightness: {main_config.tighten}")
        print(f"First Thread's initial colour: {loaded_braid.thread_states[0].color}")

    # Clean up the generated file
    if os.path.exists(OUTPUT_FILE):
        # os.remove(OUTPUT_FILE)
        pass
    print("\nDemonstration complete.")
