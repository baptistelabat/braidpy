import json
import math
from pathlib import Path
from typing import List, Optional, Literal
import urllib.parse
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, DataClassJsonMixin, config


# --- Dataclass Definitions for the Braid Structure ---
def modulo_minus_pi_pi(angle: float):
    return (angle + math.pi) % (2 * math.pi) - math.pi


@dataclass_json
@dataclass(frozen=True)
class Point(DataClassJsonMixin):
    """Represents a single 3D point (x, y, z) in a thread's path.
    The following conventions are used
    x and z are in the plane of the mobidai
    y is up for the mobidai
    z = 0 for the reference thread with is toward the right when marudai is seen from top
    """

    x: float
    y: float
    z: float


@dataclass_json
@dataclass
class Move(DataClassJsonMixin):
    """
    Represents a single crossover step in the braid pattern.
    Maps 'from_val' to 'from' and 'to_val' to 'to'.
    angle in radians
    """

    from_val: float = field(metadata=config(field_name="from"))
    to_val: float = field(metadata=config(field_name="to"))
    id: Optional[int] = None


@dataclass_json
@dataclass(frozen=True)
class AnglePosition(DataClassJsonMixin):
    """
    angle in radians
    id typically index starting from 0. Example "0"
    """

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
@dataclass
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

    repeat_from: Optional[int] = field(
        default=0, metadata=config(field_name="repeatFrom")
    )
    repeat_times: Optional[int] = field(
        default=0, metadata=config(field_name="repeatTimes")
    )
    rotate: Optional[float] = 0.0
    poss: Optional[list[AnglePosition]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Complete id

        Returns:
            None
        """
        for i, move in enumerate(self.moves):
            if move.id is None:
                self.moves[i].id = i


@dataclass_json
@dataclass
class BraidModel(DataClassJsonMixin):
    """
    Represents the complete 3D braid structure and configuration.
    The configuration parameters (tighten, rotate, repeat_from, repeat_times)
    are now assumed to be within the first element of the 'steps' list.
    """

    n_strands: int = field(metadata=config(field_name="nThreads"))

    # Nested lists of dataclasses
    thread_states: List[ThreadState] = field(
        metadata=config(field_name="threadStates"), default_factory=list
    )
    # The 'steps' list, which contains all move blocks and config info
    steps: List[Step] = field(metadata=config(field_name="steps"), default_factory=list)

    def __post_init__(self) -> None:
        """
        Complete the positions from initial state

        Returns:
            None
        """
        if not self.steps:
            self.steps = [
                Step(
                    type=None,
                    poss=[
                        AnglePosition(
                            angle=modulo_minus_pi_pi(thread_state.dir_val), id=str(i)
                        )
                        for (i, thread_state) in enumerate(self.thread_states)
                    ],
                )
            ]

        for i, step in enumerate(self.steps):
            if step.num is None:
                self.steps[i].num = i
            if step.poss is None:
                self.steps[i].poss = [
                    AnglePosition(
                        angle=modulo_minus_pi_pi(thread_state.dir_val), id=str(i)
                    )
                    for (i, thread_state) in enumerate(self.thread_states)
                ]

    def get_main_config(self) -> Step:
        """Returns the configuration from the first (and assumed only) Step element."""
        if not self.steps:
            # Return a default step if the list is empty to prevent errors
            return Step()
        return self.steps[0]

    def add_step(self, step: Step) -> None:
        """
        Add step to list of steps

        Args:
            step(Step): step to be added

        Returns:
            None
        """
        if not step.poss:
            step.poss = [
                AnglePosition(angle=thread_state.dir_val, id=str(i))
                for (i, thread_state) in enumerate(self.thread_states)
            ]
            if step.type == "threadMove":
                for move in step.moves:
                    for i, thread_state in enumerate(self.thread_states):
                        if i == move.id:
                            self.thread_states[i].dir_val = modulo_minus_pi_pi(
                                move.to_val
                            )
            #         step.poss = [
            #             AnglePosition(angle=modulo_minus_pi_pi(move.to_val), id=str(i))
            #             if i==move.id else AnglePosition(angle=modulo_minus_pi_pi(thread_state.dir_val), id=str(i))
            #             for (i, thread_state) in enumerate(self.thread_states)
            #         ]

        self.steps.append(step)

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
            f"  Threads: {self.n_strands},\n"
            f"  Repeat: {main_config.repeat_times} times (starting from move {main_config.repeat_from}),\n"
            f"  Rotation: {main_config.rotate:.4f} rad,\n"
            f"  Tightness: {main_config.tighten},\n"
            f"  Moves in Pattern ({steps_count}): {steps_summary}\n"
            f")"
        )

    def save_to_file(self, filepath: str, encode=True):
        """
        Saves the BraidModel configuration to a URL-encoded JSON file using dataclasses-json.
        """
        # Use dataclasses_json to get the JSON string, ensuring field names are correct
        json_data = self.to_json(indent=4)

        # Recursive function to convert 0.0 → 0
        def convert_floats(obj):
            if isinstance(obj, float) and obj == 0.0:
                return 0
            elif isinstance(obj, list):
                return [convert_floats(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            else:
                return obj

        # Apply the conversion
        json_data = convert_floats(json_data)

        # Write it back
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        compact_json = json.dumps(json.loads(json_data), separators=(",", ":"))

        # URL-encode the JSON string before writing
        if encode:
            data = urllib.parse.quote(compact_json)
        else:
            data = json_data

        with open(filepath, "w") as f:
            f.write(data)
        print(f"Braid model successfully saved to file: {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["BraidModel"]:
        """
        Loads a BraidModel configuration from a URL-encoded JSON file using dataclasses-json.
        """
        # 1. Read the raw, potentially URL-encoded content
        with open(filepath, "r") as f:
            raw_content = f.read()

        # 2. URL-decode the content
        decoded_content = urllib.parse.unquote(raw_content)

        # --- CRITICAL: Manually parse and restructure the flat JSON to fit the Step class ---
        data = json.loads(decoded_content)
        with open(Path(filepath).with_suffix(".json"), "w") as f:
            json.dump(data, f, indent=4)

        # 3. Load the BraidModel from the restructured dict
        model = cls.from_dict(data)

        print(f"Braid model successfully loaded and decoded from: {filepath}")
        return model

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
        code.append(f"    n_threads={self.n_strands},")  # Initial thread count
        code.append("    thread_states=[")
        # Thread states are too complex/long to print, so we'll call the external mock function
        code.append(f"        *create_initial_braid_data(num_threads={self.n_strands})")
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


def create_initial_braid_data(n_strands: int = 5) -> List[ThreadState]:
    """Creates mock initial data for demonstration, returning ThreadState dataclasses."""
    states: List[ThreadState] = []
    base_color = 0xAAAAAA

    for i in range(n_strands):
        angle = (2 * math.pi / n_strands) * i
        radius = 20.0
        initial_points = [
            Point(
                x=0.1 * radius * math.cos(angle), y=0, z=0.1 * radius * math.sin(angle)
            ),
            Point(
                x=0.7 * radius * math.cos(angle),
                y=0.7 * radius * 0.4,
                z=0.7 * radius * math.sin(angle),
            ),
            Point(
                x=0.9 * radius * math.cos(angle),
                y=0.9 * radius * 0.4,
                z=0.9 * radius * math.sin(angle),
            ),
        ]

        states.append(
            ThreadState(
                color=base_color + (i * 100000),
                dir_val=angle,
                poss=initial_points,
            )
        )
    return states
