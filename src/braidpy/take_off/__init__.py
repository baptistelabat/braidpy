# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
take_off
========

A braid as it comes off whatever made it: laid, drawn in, and tightened.

Everything here works from one thing only — where each strand's carrier was,
in a plane, over time (:class:`StrandTrajectories`).  A horn gear machine,
a braid word, a kumihimo disk: each says where its strands go, and from then
on the braid is made the same way.

- :func:`~braidpy.horn_gear.take_off.carrier_trajectories` follows the bobbins
  of a horn gear machine.
- :func:`parametric_trajectories` reads a
  :class:`~braidpy.parametric_braid.ParametricBraid`, and
  :func:`braid_word_trajectories` a braid word through it — so anything that
  produces a word, kumihimo included, can be laid.
- :func:`disk_trajectories` moves strands between the slots of a disk, and
  :func:`mobidai_trajectories` and :func:`kumihimo_trajectories` read a
  mobidai or a kumihimo sequence into it — the motion, for animating.  For
  the braid itself, :func:`mobidai_braid` and :func:`kumihimo_braid` keep
  only the crossings the moves make and lay them round a ring
  (:func:`disk_braid`): where a disk's strands wait is not where a braid
  holds them.

Laying
------
The braid is drawn off along the axis square to that plane at a steady rate,
and a yarn is taken to stay where its carrier put it.  The piece laid at time
``t`` sits over the point the carrier occupied then, carried up by the braid
taken off since:

    yarn(t) = (x(t), y(t), take_off * (T - t))

for a braid observed at time ``T``.  That gets the *topology* exactly: which
yarn passes which, and on which side.

The fell
--------
Real yarns run straight from their carriers up to the *fell*, where the braid
forms, at ``fell_height``: a ring about the size of the braid itself, yarns
being as thick as they are.  Above it each level of the braid is the
carriers' footprint drawn in toward the axis by a factor ``k``: the fell's
own size at the fell — by default the braid's own, as tight as the yarn
allows (:func:`jammed_contraction`); ``k = 0`` is the idealised braiding
point, every yarn meeting at one point — and away from it as tight as the
yarn allows.  Any positive ``k`` at each level
keeps which yarn passes over which, so the braid made is the braid kept.

Tightening
----------
:func:`tighten_yarns` then shortens every yarn under tension, keeping every
point at its height and no two yarns closer than a diameter — the problem of
*Solving a braid's shape numerically*.  Far from the fell the braid settles to
the shape its yarns pull it into, whatever the fell started it as.

Its parts
---------
Each name is imported from here; it is kept in one of

- :mod:`braidpy.take_off.paths`: the trajectories a braid is laid from, and the yarns laid;
- :mod:`braidpy.take_off.laying`: laying them, drawn in to the fell;
- :mod:`braidpy.take_off.contact`: contact between yarns, and how fast and how tight they allow;
- :mod:`braidpy.take_off.tighten`: tightening;
- :mod:`braidpy.take_off.drawing`: drawing the yarns;
- :mod:`braidpy.take_off.sources`: where strands go, from a braid word, a disk, a mobidai or a kumihimo;
- :mod:`braidpy.take_off.ring`: a disk's braid, laid round a ring.
"""

from .contact import (
    _closest_approach as _closest_approach,
)
from .contact import (
    _level_pairs as _level_pairs,
)
from .contact import (
    _offsets as _offsets,
)
from .contact import (
    jammed_contraction,
    least_take_off,
)
from .drawing import (
    _outline_traces as _outline_traces,
)
from .drawing import (
    visualize_yarns,
)
from .laying import (
    default_take_off,
    lay_yarns,
)
from .paths import (
    StrandTrajectories,
    YarnPaths,
)
from .ring import (
    _slides as _slides,
)
from .ring import (
    crossing_rows,
    disk_annular_word,
    disk_braid,
    disk_crossing_steps,
    disk_crossings,
    kumihimo_braid,
    mobidai_braid,
    ring_trajectories,
)
from .sources import (
    _disk_point as _disk_point,
)
from .sources import (
    braid_word_trajectories,
    disk_trajectories,
    kumihimo_steps,
    kumihimo_trajectories,
    mobidai_steps,
    mobidai_trajectories,
    parametric_trajectories,
)
from .tighten import (
    SAFE_STEP,
    longest_step,
    tighten_yarns,
    warn_if_too_coarse,
)
from .tighten import (
    _tension_solver as _tension_solver,
)

__all__ = [
    "SAFE_STEP",
    "StrandTrajectories",
    "YarnPaths",
    "braid_word_trajectories",
    "crossing_rows",
    "default_take_off",
    "disk_annular_word",
    "disk_braid",
    "disk_crossing_steps",
    "disk_crossings",
    "disk_trajectories",
    "jammed_contraction",
    "kumihimo_braid",
    "kumihimo_steps",
    "kumihimo_trajectories",
    "lay_yarns",
    "least_take_off",
    "longest_step",
    "mobidai_braid",
    "mobidai_steps",
    "mobidai_trajectories",
    "parametric_trajectories",
    "ring_trajectories",
    "tighten_yarns",
    "visualize_yarns",
    "warn_if_too_coarse",
]
