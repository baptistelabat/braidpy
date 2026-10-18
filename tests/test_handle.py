# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braiding machine worked by hand: braidpy.horn_gear.handle, and Braid
Studio's use of it."""

import pytest

from braidpy.horn_gear.examples import flat_braid_9, tubular_braid_8
from braidpy.horn_gear.handle import Handle, origin, sweep, turn
from braidpy.horn_gear.layout import carrier_xy
from braidpy.horn_gear.simulation import simulate


def _own(machine):
    own = machine.default_carriers()
    return [own[k] for k in sorted(own)]


@pytest.mark.parametrize("make", [flat_braid_9, tubular_braid_8])
def test_turning_the_handle_is_the_machine_running(make):
    machine = make()
    loading = _own(machine)
    history = simulate(machine, 12, dict(enumerate(loading)))
    for t in (0, 1, 5, 12):
        turned = turn(machine, loading, t)
        assert turned.time == t and not turned.met
        assert turned.positions == [c.position for c in history[t].carriers]


def test_the_handle_stops_where_carriers_meet():
    """Two carriers either side of a contact are on one point already."""
    machine = flat_braid_9()
    turned = turn(machine, [("A", 0), ("B", 2)], 10)
    assert turned.time == 0
    assert set(turned.met) == {("A", 0), ("B", 2)}


def test_two_carriers_on_one_slot_have_met_before_anything_moves():
    turned = turn(flat_braid_9(), [("A", 0), ("A", 0)], 3)
    assert turned.time == 0
    assert turned.met == {("A", 0): [0, 1]}


def test_turned_back_is_turned_one_step_fewer():
    handle = Handle(flat_braid_9())
    assert handle.turn(4).time == 4
    assert handle.back().time == 3
    assert handle.back(10).time == 0


@pytest.mark.parametrize("make", [flat_braid_9, tubular_braid_8])
def test_a_carrier_at_a_later_step_comes_from_its_slot_in_the_loading(make):
    machine = make()
    loading = _own(machine)
    for t in (1, 3, 7):
        for start, now in zip(loading, turn(machine, loading, t).positions):
            assert origin(machine, now, t) == start


def test_a_carrier_put_on_later_is_loaded_where_it_would_have_come_from():
    machine = flat_braid_9()
    handle = Handle(machine, [("A", 0)]).turn(3)
    now = turn(machine, [("C", 0)], 3).positions[0]
    handle.toggle(now)
    assert handle.loading == [("A", 0), ("C", 0)]
    handle.toggle(now)
    assert handle.loading == [("A", 0)]


def test_the_sweep_draws_what_the_animation_draws():
    """The first picture is the carriers where carrier_xy puts them, the
    last is nearly the next step: Braid Studio draws what plotly draws."""
    from braidpy.horn_gear.handle import drawing

    machine = flat_braid_9()
    state = turn(machine, _own(machine), 2).state
    layout, offsets, riding = drawing(machine)
    slots, slot_xy, carriers = sweep(machine, state, 4)
    assert len(slots) == machine.total_slots()
    assert len(slot_xy) == len(carriers) == 4
    for c, xy in zip(state.carriers, carriers[0]):
        assert xy == pytest.approx(
            carrier_xy(machine, layout, offsets, riding, c.position, 2)
        )


def test_the_handle_draws_with_plotly():
    machine = flat_braid_9()
    assert len(Handle(machine).figure().frames) == 1
    assert len(Handle(machine).turn(3).figure(n_substeps=2).frames) == 3 * 2 + 1


def test_where_carriers_met_is_ringed_in_plotly():
    figure = Handle(flat_braid_9(), [("A", 0), ("B", 2)]).figure()
    rings = [t for t in figure.data if t.name == "Met"]
    assert len(rings) == 1 and len(rings[0].x) == 2


def test_braid_studio_turns_a_catalogued_machine():
    from braidpy.web import machine_geometry, machine_origin, machine_turned

    loading = machine_geometry("flat_9")["loading"]
    turned = machine_turned("flat_9", loading, 5, frames=3)
    assert turned["time"] == 5 and turned["met"] == []
    assert len(turned["carriers"]) == len(loading)
    assert len(turned["frames"]) == 3
    assert all(len(f["slots"]) == len(turned["slots"]) for f in turned["frames"])
    first = turned["carriers"][0]
    assert machine_origin("flat_9", first, 5) == loading[0]
    met = machine_turned("flat_9", [["A", 0], ["B", 2]], 5)
    assert met["time"] == 0 and sorted(met["met"]) == [["A", 0], ["B", 2]]
