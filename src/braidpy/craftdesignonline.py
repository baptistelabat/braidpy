import json
import os
import math
from typing import List, Optional
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
@dataclass
class ThreadState(DataClassJsonMixin):
    """
    The state of a single thread.
    Maps Python names (color, dir_val) to JSON names (colour, dir).
    color: color code. Example 15395822
    dir_val: initial angle
    """

    color: int = field(metadata=config(field_name="colour"))
    dir_val: float = field(metadata=config(field_name="dir"))
    poss: List[Point] = field(default_factory=list)  # Initial 3D path points


@dataclass_json
@dataclass(frozen=True)
class Move(DataClassJsonMixin):
    """
    Represents a single crossover step in the braid pattern.
    Uses 'field' and 'config' to map 'from_val' to 'from' and 'to_val' to 'to'.
    """

    from_val: float = field(metadata=config(field_name="from"))
    to_val: float = field(metadata=config(field_name="to"))


@dataclass_json
@dataclass(frozen=True)
class Step(DataClassJsonMixin):
    """
    Represents a single crossover step in the braid pattern.
    Uses 'field' and 'config' to map 'from_val' to 'from' and 'to_val' to 'to'.
    """

    type: str
    num: int
    moves: List[Move]  # Initial 3D path points
    tighten: Optional[int]
    rotate: Optional[float]
    repeat_from: Optional[int] = field(metadata=config(field_name="repeatFrom"))
    repeat_times: Optional[int] = field(metadata=config(field_name="repeatTimes"))


@dataclass_json
@dataclass
class BraidModel(DataClassJsonMixin):
    """
    Represents the complete 3D braid structure and configuration.
    Uses field metadata to ensure all attributes map correctly to the original JSON names.
    """

    n_threads: int = field(metadata=config(field_name="nThreads"))

    # Nested lists of dataclasses
    thread_states: List[ThreadState] = field(
        metadata=config(field_name="threadStates"), default_factory=list
    )
    # RENAMED from 'moves' to 'steps' internally, but mapped back to JSON key 'moves'
    steps: List[Step] = field(metadata=config(field_name="steps"), default_factory=list)

    def __str__(self) -> str:
        """
        Provides a human-readable summary representation of the braid model.
        """
        steps_count = len(self.steps)
        steps_summary = (
            f"[{self.steps[0]!r}, ... ({steps_count - 1} more steps)]"
            if steps_count > 1
            else str(self.steps)
        )

        return (
            f"BraidModel(\n"
            f"  Threads: {self.n_threads},\n"
            f"  Repeat: {self.repeat_times} times (starting from move {self.repeat_from}),\n"
            f"  Rotation: {self.rotate:.4f} rad,\n"
            f"  Tightness: {self.tighten},\n"
            f"  Steps ({steps_count}): {steps_summary}\n"
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

            # Load the JSON from the decoded string
            # data = json.loads(decoded_content)

            # 3. Load the BraidModel from the decoded JSON string
            model = cls.from_json(decoded_content)

            # NOTE: We can update n_threads here if the list length differs from the loaded value
            model.n_threads = len(model.thread_states)

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

        This uses the new attribute names and the dataclass structure.
        """
        code = []
        code.append("# --- Programmatic Braid Model Creation Code ---")
        code.append("from your_module import BraidModel, ThreadState, Move, Point")
        code.append("import math")

        # 1. Instantiate the Model
        code.append("\n# 1. Initialize the Braid Model")
        code.append("recreated_braid = BraidModel(")
        code.append(f"    n_threads={self.n_threads},")  # Initial thread count
        code.append(f"    tighten={self.tighten},")
        code.append(f"    rotate={self.rotate},")
        code.append(f"    repeat_from={self.repeat_from},")
        code.append(f"    repeat_times={self.repeat_times},")
        code.append("    thread_states=[")
        # Thread states are too complex/long to print, so we'll call the external mock function
        code.append(f"        *create_initial_braid_data(num_threads={self.n_threads})")
        code.append("    ],")
        code.append("    steps=[")  # Use 'steps' to match the Python attribute name
        for step in self.steps:
            code.append(
                f"        Move(from_val={step.from_val}, to_val={step.to_val}),"
            )
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

    new_braid = BraidModel(
        n_threads=len(initial_states),  # MUST provide n_threads during initialization
        tighten=0,
        rotate=math.pi / 36,  # Example rotation of 5 degrees
        repeat_from=1,
        repeat_times=5,  # Repeat the pattern 5 times
        thread_states=initial_states,
    )

    # 2. ADD STEPS (MOVES) by appending Move dataclass objects
    print("--- 2. Adding Crossover Steps ---")
    new_braid.steps.append(Move(from_val=0.5, to_val=0.6))
    new_braid.steps.append(Move(from_val=1.2, to_val=1.0))
    new_braid.steps.append(Move(from_val=0.785, to_val=0.785))
    new_braid.steps.append(Move(from_val=2.356, to_val=2.4))

    print(f"Total steps in pattern: {len(new_braid.steps)}")
    print(f"Braid pattern repeats: {new_braid.repeat_times} times.")

    # 3. WRITE TO FILE
    print(f"\n--- 3. Saving Model to {OUTPUT_FILE} ---")
    new_braid.save_to_file(OUTPUT_FILE)

    # 4. LOAD FROM FILE
    print(f"\n--- 4. Loading Model from {OUTPUT_FILE} ---")
    loaded_braid = BraidModel.load_from_file(OUTPUT_FILE)

    if loaded_braid:
        print("\n--- 5. Verification of Loaded Data ---")
        print("--- String Representation (__str__) ---")
        print(loaded_braid)

        print("\n--- Programmatic Re-creation Code ---")
        creation_code = loaded_braid.get_programmatic_code()
        print(creation_code)

        # Original verification checks (using new attribute names)
        print(f"\nLoaded Threads: {loaded_braid.n_threads}")
        print(f"Loaded Steps Count: {len(loaded_braid.steps)}")
        print(
            f"First Step (from, to): {loaded_braid.steps[0].from_val:.3f}, {loaded_braid.steps[0].to_val:.3f}"
        )
        print(
            f"Repetition Info: Repeats from index {loaded_braid.repeat_from} for {loaded_braid.repeat_times} times."
        )
        print(f"First Thread's initial colour: {loaded_braid.thread_states[0].color}")

    # Clean up the generated file
    if os.path.exists(OUTPUT_FILE):
        # os.remove(OUTPUT_FILE)
        pass  # Keep the file for inspection in a real environment
    print("\nDemonstration complete.")
