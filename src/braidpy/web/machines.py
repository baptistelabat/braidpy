# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Horn gear braiding machines: the braid a machine makes, loaded as it loads
itself or by hand, stopped where carriers meet; and the machine as the page
draws it from above, to load it by hand."""

from __future__ import annotations

import re
from typing import Any, Callable, Collection, Dict, Hashable, List, Optional, Tuple

from braidpy.web._info import _braid_info
from braidpy.web._result import _PALETTE, _result, _tighten, _timeline
from braidpy.web._settings import Machine
from braidpy.web._spec import defaults
from braidpy.web._types import Info, MachineGeometry, Result, Source, Spec


def _machines() -> Dict[str, Callable[[], Any]]:
    from braidpy.horn_gear import examples

    return {
        "flat_3": examples.flat_braid_3,
        "flat_4": examples.flat_braid_4,
        "flat_9": examples.flat_braid_9,
        "soutache_5": examples.soutache_braid,
        "soutache_7": lambda: examples.soutache_braid(n_slots=7),
        "princess": examples.princess_braid,
        "tubular_8": examples.tubular_braid_8,
        "tubular_12": examples.tubular_braid_12,
        "tubular_16": examples.tubular_braid_16,
    }


def _from_machine(spec: Spec) -> Result:
    from braidpy.horn_gear import (
        axial_positions,
        compute_layout,
        gear_radii,
        yarn_paths,
    )
    from braidpy.horn_gear.word import annular_word, flat_word

    machines = _machines()
    name = Machine.name.read(spec)
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    machine = machines[name]()
    cycles = Machine.cycles.read(spec)
    radii = gear_radii(machine)
    default = Machine.of_gear_radius * sum(radii.values()) / len(radii)
    diameter = Machine.yarn_diameter.read(spec, default=default)
    layout = compute_layout(machine)
    cores = axial_positions(machine, layout)
    stiff = Machine.cores.read(spec)
    if stiff not in Machine.stiffness:
        raise ValueError("Cores are either yarn or rigid.")
    # The cores run up the braid, each in its own place, where the machine
    # lays it; the yarns are drawn in round them.  A rigid core stays
    # straight there; a core of yarn is held there at both ends, and gives
    # way between to the yarns pressing on it — never so far as to pass
    # another core.
    # Loaded by hand, or as the machine loads itself.  Carriers that meet
    # stop the machine: the braid is what it made until then.
    loading = _loading(spec.get("carriers"), machine)
    carriers_at = None if loading is None else dict(enumerate(loading))
    stopped = None
    n_steps = None
    if carriers_at is not None:
        from braidpy.horn_gear.simulation import (
            CollisionError,
            simulate,
            state_period,
        )

        period = state_period(machine, carriers_at) or machine.contact_period()
        n_steps = cycles * period
        try:
            simulate(machine, n_steps, carriers_at)
        except CollisionError as error:
            stopped = error
            n_steps = error.step - 1
            if n_steps < 1:
                raise ValueError(
                    "Those carriers meet as soon as the machine turns: "
                    + _met(error)
                    + "."
                ) from None
    paths = yarn_paths(
        machine,
        n_steps=n_steps,
        carrier_positions=carriers_at,
        n_cycles=cycles,
        yarn_diameter=diameter,
        fell_radius=0.0,
        axials=True,
    )
    paths = _place_cores(paths, cores)
    paths = _tighten(
        paths, spec, diameter, rigid=list(cores) if stiff == "rigid" else []
    )
    info: Info = {}
    notes = ["Words are read over one cycle of the machine."]
    if stopped is not None:
        # The carriers that met, where they started: as the page draws
        # the machine, before it turns.
        assert loading is not None
        info["collision"] = {
            "step": int(stopped.step),
            "at": [
                [loading[k][0], int(loading[k][1])]
                for ids in stopped.collisions.values()
                for k in ids
            ],
        }
        notes = [
            f"Carriers met at step {stopped.step}, on {_met(stopped)}: the "
            f"braiding stopped there, after {n_steps} steps. The carriers that "
            "met are ringed where they started. No word is read."
        ]
    elif cores:
        notes = [
            "It braids round a core, drawn here in grey as the yarn it is; its "
            "word would need the core as a strand of its own: no word is given."
        ]
    elif name.startswith("tubular"):
        annular = annular_word(machine, carriers=carriers_at)
        info["annular_word"] = " ".join(str(g) for g in annular.generators)
        info["crossings"] = len(annular.generators)
    else:
        # Read over one cycle of the machine.
        info.update(
            _braid_info(flat_word(machine, carriers=carriers_at), len(paths.points))
        )
        info["repeated"] = "cycle"
        info["made"] = cycles
        # The cycles made, not the one read.
        info["pure"] = cycles % (info.get("pure_after") or 1) == 0
    keys = list(paths.points)
    carriers = [k for k in keys if k not in cores]
    colour = {k: _PALETTE[i % len(_PALETTE)] for i, k in enumerate(carriers)}
    colour.update({k: Machine.core_colour for k in cores})
    return _result(
        Machine.titles[name] + f", {cycles} cycles",
        paths,
        diameter,
        colours=[colour[k] for k in keys],
        names=[f"Core {k}" if k in cores else f"Yarn {k}" for k in keys],
        info=info,
        notes=notes,
        timeline=_timeline(paths.trajectories, keys, "machine"),
    )


def _loading(text: Any, machine: Any) -> Optional[List[Tuple[str, int]]]:
    """Carriers given as ``gear:slot``, each once; None if not given."""
    if text is None or not str(text).strip():
        return None
    if str(text).strip().lower() == "none":
        raise ValueError("Give at least one carrier.")
    loading: List[Tuple[str, int]] = []
    for token in re.split(r"[\s,;]+", str(text).strip()):
        match = re.fullmatch(r"([^:\s]+):(\d+)", token)
        if not match:
            raise ValueError(f"Cannot read {token!r}: give each carrier as gear:slot.")
        gear, slot = match.group(1), int(match.group(2))
        if gear not in machine.gears:
            raise ValueError(f"No gear {gear!r}: one of {sorted(machine.gears)}.")
        n = machine.gears[gear].n_slots
        if slot >= n:
            raise ValueError(f"Gear {gear} has slots 0 to {n - 1}.")
        if (gear, slot) in loading:
            raise ValueError(f"Two carriers on the same slot, {gear}:{slot}.")
        loading.append((gear, slot))
    if not loading:
        raise ValueError("Give at least one carrier.")
    return loading


def _met(error: Any) -> str:
    """Where carriers met, as gear:slot."""
    return " and ".join(f"{g}:{slot}" for g, slot in error.collisions)


def machine_geometry(name: str) -> MachineGeometry:
    """A machine as the page draws it from above, to load it by hand: its
    gears — where, how big, the circle their carriers ride, their slots, the
    way they turn and where their first slot is — the contacts between them,
    and the machine's own loading.  A slot's angle at step ``t`` is
    ``offset + 2π (slot + direction · t) / slots``."""
    from braidpy.horn_gear.layout import (
        carrier_radius,
        compute_layout,
        contact_point,
        gear_radii,
        slot_offsets,
    )

    machines = _machines()
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    machine = machines[name]()
    layout = compute_layout(machine)
    radii = gear_radii(machine)
    offsets = slot_offsets(machine, layout)
    own = machine.default_carriers()
    return {
        "name": name,
        "gears": [
            {
                "name": gear_name,
                "x": float(layout[gear_name][0]),
                "y": float(layout[gear_name][1]),
                "radius": float(radii[gear_name]),
                "ride": float(carrier_radius(machine, layout, gear_name)),
                "slots": int(gear.n_slots),
                "direction": int(gear.direction),
                "offset": float(offsets[gear_name]),
            }
            for gear_name, gear in machine.gears.items()
        ],
        "contacts": [
            {
                "a": conn.gear_a,
                "b": conn.gear_b,
                "x": float(point[0]),
                "y": float(point[1]),
            }
            for conn in machine.connections
            for point in [contact_point(machine, layout, conn.gear_a, conn.gear_b)]
        ],
        "loading": [[own[k][0], int(own[k][1])] for k in sorted(own)],
    }


def _place_cores(paths, cores: Collection[Hashable]):
    """The cores, each standing straight in the braid where the machine
    lays it, all the way down to the fell: drawn in to the braiding point
    with the yarns, the cores would meet there, and could pass each other."""
    from dataclasses import replace

    if not cores:
        return paths
    points = dict(paths.points)
    n = paths.formed_count
    for k in cores:
        line = points[k].copy()
        line[:n, :2] = line[0, :2]
        points[k] = line
    return replace(paths, points=points)


def _machine_entry() -> Source:
    return {
        "title": "Horn gear braiding machine",
        "defaults": defaults(*Machine.shown),
        "entries": [
            {"name": name, "title": title} for name, title in Machine.titles.items()
        ],
    }


SOURCES: Dict[str, Tuple[Callable[[], Source], Callable[[Spec], Result]]] = {
    "machine": (_machine_entry, _from_machine)
}
