import json
import os
import math
from typing import List, Dict, Any, Optional
import urllib.parse  # <-- New: Added for URL encoding/decoding

# Define Type Aliases for clarity
# A single 3D point
Point = Dict[str, float]
# The state of a single thread (color, direction, and 3D path)
ThreadState = Dict[str, Any]
# A single crossover step
Move = Dict[str, float]


class BraidModel:
    """
    Represents a 3D braid structure based on the parameters found
    in the URL-encoded JSON file.

    It handles initialization, adding moves, and serialization (saving/loading)
    of the braid configuration to a JSON file.
    """

    def __init__(
        self,
        n_threads: int = 0,
        tighten: int = 0,
        rotate: float = 0.0,
        repeat_from: int = 1,
        repeat_times: int = 1,
    ):
        """
        Initializes the Braid Model with core parameters.

        Args:
            n_threads: The total number of threads in the braid.
            tighten: A tightening factor (0 in the original file).
            rotate: A rotational offset applied to the braid.
            repeat_from: The starting index (1-based) of the moves array for repetition.
            repeat_times: How many times the pattern (from repeat_from onwards) is repeated.
        """
        self.n_threads: int = n_threads
        self.thread_states: List[ThreadState] = []
        self.moves: List[Move] = []
        self.tighten: int = tighten
        self.rotate: float = rotate
        self.repeat_from: int = repeat_from
        self.repeat_times: int = repeat_times
        # NOTE: The 'poss' (positions) array found in the original file
        # is complex and assumed to be derived from the thread_states for a full model.

    def __str__(self) -> str:
        """
        Provides a human-readable summary representation of the braid model.
        """
        moves_count = len(self.moves)
        moves_summary = (
            f"[{self.moves[0]!r}, ... ({moves_count - 1} more moves)]"
            if moves_count > 1
            else str(self.moves)
        )

        return (
            f"BraidModel(\n"
            f"  Threads: {self.n_threads},\n"
            f"  Repeat: {self.repeat_times} times (starting from move {self.repeat_from}),\n"
            f"  Rotation: {self.rotate:.4f} rad,\n"
            f"  Tightness: {self.tighten},\n"
            f"  Moves ({moves_count}): {moves_summary}\n"
            f")"
        )

    def add_thread(self, color: int, direction: float, initial_points: List[Point]):
        """
        Adds a new thread to the model.

        Args:
            color: An integer representing the thread's color (e.g., 15395822).
            direction: A float representing the thread's initial direction/orientation.
            initial_points: A list of 3D points ({'x', 'y', 'z'}) defining the thread's initial curve.
        """
        self.thread_states.append(
            {"colour": color, "dir": direction, "poss": initial_points}
        )
        self.n_threads = len(self.thread_states)

    def add_move(self, from_val: float, to_val: float):
        """
        Adds a new crossover step (move) to the braid pattern.
        These values could represent angles, fractional indices, or other simulation parameters.

        Args:
            from_val: The 'from' parameter for the move (e.g., a starting angle).
            to_val: The 'to' parameter for the move (e.g., an ending angle).
        """
        self.moves.append({"from": from_val, "to": to_val})

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the BraidModel object into a dictionary suitable for JSON serialization.
        """
        return {
            "nThreads": self.n_threads,
            "threadStates": self.thread_states,
            "moves": self.moves,
            "tighten": self.tighten,
            "rotate": self.rotate,
            "repeatFrom": self.repeat_from,
            "repeatTimes": self.repeat_times,
            # Note: The original file had a complex 'poss' array at the root,
            # which is omitted here as it's likely a computed output.
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BraidModel":
        """
        Creates a BraidModel instance from a dictionary loaded from JSON.
        """
        model = cls(
            n_threads=data.get("nThreads", 0),
            tighten=data.get("tighten", 0),
            rotate=data.get("rotate", 0.0),
            repeat_from=data.get("repeatFrom", 1),
            repeat_times=data.get("repeatTimes", 1),
        )
        model.thread_states = data.get("threadStates", [])
        model.moves = data.get("moves", [])
        # Recalculate n_threads based on actual loaded states
        model.n_threads = len(model.thread_states)
        return model

    def save_to_file(self, filepath: str):
        """
        Saves the BraidModel configuration to a URL-encoded JSON file.
        """
        try:
            json_data = json.dumps(self.to_dict())
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
        Loads a BraidModel configuration from a URL-encoded JSON file.
        """
        try:
            # 1. Read the raw, potentially URL-encoded content
            with open(filepath, "r") as f:
                raw_content = f.read()

            # 2. URL-decode the content
            decoded_content = urllib.parse.unquote(raw_content)

            # 3. Load the JSON from the decoded string
            data = json.loads(decoded_content)

            print(f"Braid model successfully loaded and decoded from: {filepath}")
            return cls.from_dict(data)
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

        NOTE: Due to the complexity and length of the thread position data ('poss' lists),
        this function generates code to recreate the pattern and metadata,
        and uses the helper function `create_initial_braid_data()` for mock
        thread initialization. You would replace `create_initial_braid_data()`
        with your actual thread loading/generation logic.
        """
        code = []
        code.append("# --- Programmatic Braid Model Creation Code ---")
        code.append("import math")
        # NOTE: Assumes BraidModel and create_initial_braid_data are available in the target scope
        code.append("from your_module import BraidModel, create_initial_braid_data")

        # 1. Instantiate the Model
        code.append("\n# 1. Initialize the Braid Model")
        code.append("recreated_braid = BraidModel(")
        code.append(f"    repeat_from={self.repeat_from},")
        code.append(f"    repeat_times={self.repeat_times},")
        code.append(f"    rotate={self.rotate},")
        code.append(f"    tighten={self.tighten}")
        code.append(")")

        # 2. Add Thread States (using the mock function for brevity)
        code.append("\n# 2. Add thread states (uses mock generator for demonstration)")
        code.append(f"num_threads_to_add = {self.n_threads}")
        code.append(
            "initial_states = create_initial_braid_data(num_threads=num_threads_to_add)"
        )
        code.append("for state in initial_states:")
        code.append(
            "    # Note: Using .thread_states.append() for simplicity since 'poss' is mock data"
        )
        code.append("    recreated_braid.thread_states.append(state)")
        code.append("recreated_braid.n_threads = len(recreated_braid.thread_states)")

        # 3. Add Moves
        code.append("\n# 3. Add Crossover Steps (Moves)")
        for move in self.moves:
            code.append(
                f"recreated_braid.add_move(from_val={move['from']}, to_val={move['to']})"
            )

        code.append("\n# 4. Print Verification")
        code.append("print('Braid Model Recreated Successfully:')")
        code.append("print(recreated_braid)")

        return "\n".join(code)


# --- Demonstration of BraidModel Usage ---


def create_initial_braid_data(num_threads: int = 5) -> List[ThreadState]:
    """Creates mock initial data for demonstration."""
    states: List[ThreadState] = []
    # Base color (simple gray to demonstrate structure)
    base_color = 0xAAAAAA

    for i in range(num_threads):
        # Initial positions: arrange in a circle on the XY plane
        angle = (2 * math.pi / num_threads) * i
        radius = 5.0
        initial_points = [
            {"x": radius * math.cos(angle), "y": radius * math.sin(angle), "z": 0.0},
            {"x": radius * math.cos(angle), "y": radius * math.sin(angle), "z": 1.0},
            {
                "x": radius * math.cos(angle) * 0.9,
                "y": radius * math.sin(angle) * 0.9,
                "z": 2.0,
            },
        ]

        # Assign unique properties
        states.append(
            {
                "colour": base_color + (i * 100000),
                "dir": 0.1 + (i * 0.05),  # Example direction/orientation
                "poss": initial_points,
            }
        )
    return states


if __name__ == "__main__":
    loaded_braid = BraidModel.load_from_file("/home/baptiste/Downloads/braid (1).b3d")
    OUTPUT_FILE = "new_braid_config.json"

    # 1. CREATE A NEW BRAID MODEL (Simulating the core structure)
    print("--- 1. Creating a New Braid Model ---")
    new_braid = BraidModel(
        repeat_from=1,
        repeat_times=5,  # Repeat the pattern 5 times
        rotate=math.pi / 36,  # Example rotation of 5 degrees
    )

    # Add 5 mock threads
    initial_states = create_initial_braid_data(num_threads=5)
    for state in initial_states:
        new_braid.thread_states.append(state)
    new_braid.n_threads = len(initial_states)

    # 2. ADD STEPS (MOVES)
    # Assuming moves are angles in radians for relative thread displacement
    print("--- 2. Adding Crossover Steps ---")
    new_braid.add_move(from_val=0.5, to_val=0.6)  # Small crossover
    new_braid.add_move(from_val=1.2, to_val=1.0)  # Backwards move
    new_braid.add_move(from_val=0.785, to_val=0.785)  # No net angular change (pi/4)
    new_braid.add_move(from_val=2.356, to_val=2.4)  # Crossover near 3pi/4

    print(f"Total moves in pattern: {len(new_braid.moves)}")
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

        # Original verification checks (kept for comparison)
        print(f"\nLoaded Threads: {loaded_braid.n_threads}")
        print(f"Loaded Moves Count: {len(loaded_braid.moves)}")
        print(
            f"First Move (from, to): {loaded_braid.moves[0]['from']:.3f}, {loaded_braid.moves[0]['to']:.3f}"
        )
        print(
            f"Repetition Info: Repeats from index {loaded_braid.repeat_from} for {loaded_braid.repeat_times} times."
        )
        print(
            f"First Thread's initial colour: {loaded_braid.thread_states[0]['colour']}"
        )

    # Clean up the generated file
    if os.path.exists(OUTPUT_FILE):
        # os.remove(OUTPUT_FILE)
        pass  # Keep the file for inspection in a real environment
    print("\nDemonstration complete.")
