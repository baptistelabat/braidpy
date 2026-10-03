# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/jacquard.py
=====================

Jacquard lace machine: a braiding machine whose gears are driven one by one
from a punched programme instead of being geared together.

An ordinary braiding machine turns every gear on every step, so its braid is
fixed by the wiring of the machine.  A Jacquard machine reads, at each step of
its programme, a **two-line binary mask** over the gears:

- the first line says which gears take a half turn **trigonometrically** (CCW),
- the second line says which take a half turn **clockwise**.

A gear's *direction* belongs to the gear and never changes; the mask only says
whether it is allowed to turn this step.

What makes this machine different is its geometry.  Its gear circles
**interpenetrate** rather than merely touching, and a slot is the notch cut
where two of them overlap — so a slot belongs to *both* gears at once, and a
bobbin sitting in one is swept out by whichever of the pair turns.  That is
what lets a gear turn while its neighbour stands still, which a machine of
tangent gears cannot do.

It also means two neighbouring gears must never turn together: they would both
reach for the bobbin in the notch they share.  Hence the two lines, driven one
after the other — neighbours alternate direction round a ring, so each line on
its own only ever turns gears that do not touch.  A programme that breaks this
is rejected when the machine is built.

Because the programme decides where every bobbin goes, a bobbin's path need
not come back on itself: there are no closed tracks here and no period, and
:func:`~braidpy.horn_gear.tracks.compute_tracks` and its relatives say so
rather than inventing one.  Thread the machine with :func:`notch_positions`
and simulate the programme instead.

Layout, drawing and collision detection are shared with any other machine and
need no special case: the only things that differ are how far each gear has
turned by a given step and where a bobbin goes next, both of which the base
class already asks itself through
:meth:`~braidpy.horn_gear.model.BraidingMachine.rotation` and
:meth:`~braidpy.horn_gear.model.BraidingMachine.next_position`.
"""

from __future__ import annotations

import math
from math import gcd, lcm
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import networkx as nx

from .model import Axial, BraidingMachine, Connection, HornGear

# One line of a mask: a bit per gear, as "1011", (1, 0, 1, 1) or (True, ...).
MaskLine = Union[str, Sequence[Union[int, bool]]]

# One programmed step: (trigonometric line, clockwise line).
ProgramStep = Tuple[MaskLine, MaskLine]


class JacquardProgramError(ValueError):
    """Raised when a programme cannot be run on this machine."""


def _parse_line(line: MaskLine, n_gears: int, where: str) -> Tuple[bool, ...]:
    """Turn one mask line into a tuple of flags, one per gear."""
    if isinstance(line, str):
        stripped = line.strip().replace(" ", "")
        if any(ch not in "01" for ch in stripped):
            raise JacquardProgramError(
                f"{where}: mask line {line!r} may only contain 0 and 1."
            )
        bits: Tuple[bool, ...] = tuple(ch == "1" for ch in stripped)
    else:
        bits = tuple(bool(b) for b in line)

    if len(bits) != n_gears:
        raise JacquardProgramError(
            f"{where}: mask line has {len(bits)} bits but the machine has "
            f"{n_gears} gears."
        )
    return bits


def notch_positions(machine: "JacquardLaceMachine") -> Dict[int, Tuple[str, int]]:
    """One bobbin in every notch — the usual way a lace machine is threaded.

    A notch is shared by the two gears whose circles cut it, so there is one
    bobbin position per contact, not per slot.  Filling them all is safe by
    construction: no two bobbins can land in the same notch.

    Args:
        machine: The machine to thread.

    Returns:
        Dict mapping carrier_id → (gear_name, slot), one entry per contact.
    """
    return {
        index: (conn.gear_a, conn.slot_a0)
        for index, conn in enumerate(machine.connections)
    }


class JacquardLaceMachine(BraidingMachine):
    """A braiding machine whose gears are driven individually by a programme.

    Args:
        gears: The horn gears.  Lace machines use 2-slot gears, but any slot
            count works.
        connections: Contacts between gears, as for any machine.
        program: One entry per programmed step, each a
            ``(trigonometric_line, clockwise_line)`` pair.  A line is a bit per
            gear, in the order the gears were given — ``"1010"``, ``(1, 0, 1, 0)``
            or a tuple of bools.
        axials: Optional cords the braid forms around.

    Raises:
        JacquardProgramError: If the programme is empty, a line is the wrong
            length, a line enables a gear that turns the other way, or a line
            turns two neighbouring gears at once.
    """

    #: The circles overlap, and a slot is the notch they cut between them.
    gears_interpenetrate: bool = True

    #: Carriers go where the programme sends them, so their paths need not
    #: close and the machine has no tracks or period to compute.
    has_fixed_tracks: bool = False

    def __init__(
        self,
        gears: List[HornGear],
        connections: List[Connection],
        program: Sequence[ProgramStep],
        axials: Iterable[Axial] = (),
    ) -> None:
        super().__init__(gears, connections, axials)

        if not program:
            raise JacquardProgramError("A Jacquard machine needs a programme.")

        names = list(self.gears)
        self.program: List[Tuple[Tuple[bool, ...], Tuple[bool, ...]]] = []
        phases: List[FrozenSet[str]] = []

        for index, entry in enumerate(program):
            if len(entry) != 2:
                raise JacquardProgramError(
                    f"step {index}: expected a (trigonometric, clockwise) pair, "
                    f"got {len(entry)} lines."
                )
            ccw = _parse_line(entry[0], len(names), f"step {index} trigonometric")
            cw = _parse_line(entry[1], len(names), f"step {index} clockwise")

            # A gear turns the way it is built to turn; a line may only enable
            # the gears that already turn that way.
            for line, wanted, label in (
                (ccw, 1, "trigonometric"),
                (cw, -1, "clockwise"),
            ):
                for name, on in zip(names, line):
                    if on and self.gears[name].direction != wanted:
                        raise JacquardProgramError(
                            f"step {index}: the {label} line enables gear "
                            f"'{name}', which turns the other way."
                        )

            self.program.append((ccw, cw))
            # The two lines are driven one after the other, so each is a phase
            # of its own.  Within a phase no two enabled gears may touch, or
            # they would fight over the notch they share.
            for line, label in ((ccw, "trigonometric"), (cw, "clockwise")):
                enabled = frozenset(n for n, on in zip(names, line) if on)
                for a, b in self.graph.edges():
                    if a in enabled and b in enabled:
                        raise JacquardProgramError(
                            f"step {index}: the {label} line turns '{a}' and "
                            f"'{b}' together, but they share a notch and would "
                            f"fight over the bobbin in it."
                        )
                phases.append(enabled)

        self._phases: List[FrozenSet[str]] = phases

        # Turns per gear over one pass of the programme, and after each phase
        # within it, so rotation() is O(1) rather than a walk from t=0.
        self._per_cycle: Dict[str, int] = {n: 0 for n in names}
        self._prefix: List[Dict[str, int]] = [dict(self._per_cycle)]
        running = dict(self._per_cycle)
        for turning in phases:
            for name in turning:
                running[name] += 1
            self._prefix.append(dict(running))
        self._per_cycle = running

    # ── How the gears are driven ──────────────────────────────────────────

    def turning_gears(self, step: int) -> FrozenSet[str]:
        """Gears enabled for the phase running from ``step`` to ``step + 1``."""
        return self._phases[step % len(self._phases)]

    def program_rows(self) -> List[Tuple[str, Tuple[bool, ...]]]:
        """The programme as punchcard rows, two per punched step."""
        rows: List[Tuple[str, Tuple[bool, ...]]] = []
        for ccw, cw in self.program:
            rows.append(("trigonometric", ccw))
            rows.append(("clockwise", cw))
        return rows

    def preferred_layout(
        self, scale: float = 1.0
    ) -> Optional[Dict[str, Tuple[float, float]]]:
        """Place a ring so every notch lands exactly on a slot.

        The generic layout sets gear circles *tangent*, which is right for a
        braiding machine but wrong here: these circles have to overlap for
        there to be a notch at all.  For a ring of ``n`` gears of 2 slots the
        geometry is forced, and worth deriving rather than approximating.

        A gear's two notches are cut where its circle crosses each neighbour's,
        and being 2-slot they must come out diametrically opposite — so the
        gear's centre is the midpoint of the two notches.  Putting the centres
        on a circle of radius ``R`` and working that condition through gives::

            r = R * tan(pi / n)

        which is larger than the ``R * sin(pi / n)`` half-spacing that would
        make them touch, so the circles interpenetrate exactly as they should.

        Returns None — deferring to the generic layout — for anything that is
        not a ring of equal 2-slot gears.

        Args:
            scale: Overall scale factor for gear radii.

        Returns:
            Gear name → (x, y), or None.
        """
        from .layout import _gear_radius

        n = len(self.gears)
        if n < 3 or any(gear.n_slots != 2 for gear in self.gears.values()):
            return None
        if any(degree != 2 for _, degree in self.graph.degree()):
            return None

        cycles = nx.cycle_basis(self.graph)
        if len(cycles) != 1 or len(cycles[0]) != n:
            return None

        radius = _gear_radius(2, scale)
        ring_radius = radius / math.tan(math.pi / n)
        return {
            name: (
                ring_radius * math.cos(2 * math.pi * i / n),
                ring_radius * math.sin(2 * math.pi * i / n),
            )
            for i, name in enumerate(cycles[0])
        }

    def riding_position(self, pos: Tuple[str, int], time: int) -> Tuple[str, int]:
        """Which gear sweeps a bobbin through this step — which may not be its own.

        A bobbin in a notch is swept by whichever of the two gears turns, so
        the gear that moves it is the one it *ends* the step on.  Drawing it on
        its own idle gear instead would leave it still for the whole step and
        then jump it across to the neighbour.

        All three cases fall out of :meth:`next_position`: the bobbin's own
        gear when that turns, the receiving gear when the neighbour takes it,
        and where it already is when nothing moves.
        """
        return self.next_position(pos, time)

    def default_carriers(self) -> Dict[int, Tuple[str, int]]:
        """Thread one bobbin into every notch."""
        return notch_positions(self)

    def next_position(self, pos: Tuple[str, int], time: int) -> Tuple[str, int]:
        """Where a carrier goes during the step from ``time`` to ``time + 1``.

        The gear circles interpenetrate, so a slot is the notch cut where two
        of them overlap and **belongs to both gears at once**.  A bobbin
        sitting in that notch is swept out by whichever of the two turns:

        - its own gear turns → it stays on that gear, carried round to the
          gear's other notch;
        - its own gear is idle and the gear across the notch turns → that gear
          takes it, and it rides on round to *that* gear's other notch;
        - neither turns → it stays where it is.

        Both turning at once would have the two gears fighting over the same
        bobbin, which is why the mask is split into two lines and applied one
        after the other; the constructor rejects a line that enables
        neighbouring gears together.

        Args:
            pos: Current (gear_name, slot_index).
            time: Step being taken.

        Returns:
            The (gear_name, slot_index) the carrier occupies afterwards.
        """
        gear_name, slot = pos
        turning = self.turning_gears(time)

        if gear_name in turning:
            return pos  # swept round to this gear's other notch

        # Idle gear: the neighbour sharing this notch may take the bobbin.
        # Read the contact as it stands now, before either gear moves.
        neighbor = self.neighbor_at_slot(gear_name, slot, time)
        if neighbor is not None and neighbor[0] in turning:
            return neighbor

        return pos

    def rotation(self, gear_name: str, time: int) -> int:
        """Signed slots turned through after ``time`` simulation steps."""
        cycles, rest = divmod(time, len(self._phases))
        turns = cycles * self._per_cycle[gear_name] + self._prefix[rest][gear_name]
        return self.gears[gear_name].direction * turns

    def contact_period(self) -> int:
        """Steps until the programme restarts *and* every gear is back square.

        The programme repeats every ``steps_per_pass`` steps, but a gear only
        looks the same again once its accumulated turns are a whole number of
        revolutions, so the true period is a multiple of the programme length.
        """
        multiple = 1
        for name, gear in self.gears.items():
            net = self.rotation(name, self.steps_per_pass) % gear.n_slots
            if net:
                multiple = lcm(multiple, gear.n_slots // gcd(net, gear.n_slots))
        return multiple * self.steps_per_pass

    # ── Reading the programme ─────────────────────────────────────────────

    @property
    def steps_per_pass(self) -> int:
        """Simulation steps in one pass of the programme — two per punched step.

        The two mask lines are driven one after the other, so a punched step
        takes two simulation steps.
        """
        return len(self._phases)


def jacquard_lace_ring(
    n_gears: int = 6,
    program: Sequence[ProgramStep] | None = None,
    n_slots: int = 2,
) -> JacquardLaceMachine:
    """A tubular Jacquard lace machine: 2-slot gears in a ring.

    Layout::

        [A] - [B] - [C] - [D] - [E] - [F] - back to [A]

    Each gear carries two slots, one at each of its two contacts, so a half
    turn swaps which neighbour each of its carriers faces.  Gears alternate
    direction round the ring, which is why ``n_gears`` must be even — meshing
    gears have to turn opposite ways.

    With no programme given, every gear is enabled on every step, which drives
    the machine exactly like an ordinary tubular braider and is the useful
    baseline to compare a real programme against.

    Args:
        n_gears: Number of gears in the ring; must be even and at least 4.
        program: Punched steps; defaults to one step with everything enabled.
        n_slots: Slots per gear.  Lace machines use 2.

    Returns:
        JacquardLaceMachine for a ring of gears.

    Raises:
        ValueError: If ``n_gears`` is odd or smaller than 4.
    """
    if n_gears < 4 or n_gears % 2:
        raise ValueError(
            f"A ring needs an even number of at least 4 gears, got {n_gears}. "
            "Neighbouring gears mesh, so they must turn opposite ways."
        )

    names = [chr(ord("A") + i) for i in range(n_gears)]
    gears = [
        HornGear(name, n_slots, direction=+1 if i % 2 == 0 else -1)
        for i, name in enumerate(names)
    ]
    # Slot 0 of each gear faces the next gear round the ring, slot 1 the previous.
    connections = [
        Connection(
            names[i],
            names[(i + 1) % n_gears],
            slot_a0=0,
            slot_b0=n_slots - 1,
            name=f"{names[i]}-{names[(i + 1) % n_gears]}",
        )
        for i in range(n_gears)
    ]

    if program is None:
        # Every gear enabled: the trigonometric line drives the CCW gears and
        # the clockwise line the CW ones.  Neighbours alternate direction, so
        # neither line ever turns two touching gears together.
        ccw = "".join("1" if i % 2 == 0 else "0" for i in range(n_gears))
        cw = "".join("0" if i % 2 == 0 else "1" for i in range(n_gears))
        program = [(ccw, cw)]

    return JacquardLaceMachine(gears, connections, program)
