# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What a braid is laid from and what it is laid as: where each strand's
carrier was over time (:class:`StrandTrajectories`), and the yarns laid
from it (:class:`YarnPaths`)."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

import numpy as np

from .contact import _closest_approach


@dataclass(frozen=True)
class StrandTrajectories:
    """Where every strand's carrier went, sampled over time.

    This is all the rest of the module needs: a braid is laid from it, drawn
    in and tightened without knowing what made it.

    Args:
        times: Time of each sample, evenly spaced; shape ``(n,)``.  The units
            are whatever the source counts in — machine steps, moves, or the
            0 to 1 of a parametric strand — and ``take_off`` is per unit.
        xy: Per strand, its position in the plane at each of those times;
            shape ``(n, 2)``.
        outlines: Closed curves to draw on the plane under the braid — the
            gears, a disk's rim — each of shape ``(m, 2)``.
        axis: The braid's axis in the plane, if the source knows where it is;
            the middle of the samples otherwise.
        label: Prefix naming a strand in a drawing, followed by its key.
        outline_name: What the outlines are, in a drawing's legend.
        slots: Named places in the plane to mark in a drawing — a disk's
            slots — as ``(x, y, name)``.
    """

    times: np.ndarray
    xy: dict[Hashable, np.ndarray]
    outlines: tuple[np.ndarray, ...] = ()
    axis: tuple[float, float] | None = None
    label: str = "Yarn "
    outline_name: str = "Deck"
    slots: tuple[tuple[float, float, str], ...] = ()

    def __post_init__(self) -> None:
        if len(self.times) < 2:
            raise ValueError("Trajectories need at least two samples.")
        steps = np.diff(self.times)
        if np.any(steps <= 0) or not np.allclose(steps, steps[0]):
            raise ValueError("Trajectory samples must be evenly spaced in time.")
        for key, xy in self.xy.items():
            if np.shape(xy) != (len(self.times), 2):
                raise ValueError(f"Strand {key!r}: expected {len(self.times)} (x, y).")

    def centre(self) -> tuple[float, float]:
        """The braid's axis: the source's, or the middle of every sample."""
        if self.axis is not None:
            return self.axis
        every = np.concatenate(list(self.xy.values()))
        return float(every[:, 0].mean()), float(every[:, 1].mean())


@dataclass(frozen=True)
class YarnPaths:
    """The yarns of a braid, as they stand at one instant.

    Args:
        times: When each point of a yarn was laid, in the trajectories' units; shape ``(n,)``.
        points: Per strand, its yarn's centreline; shape ``(n, 3)``, in the
            same order as ``times``, so the last point is the one at the deck, where the yarn leaves its carrier.
        take_off: Length of braid drawn off per unit of time.
        trajectories: The strand motion the yarns were laid from.
        fell_height: Height of the fell over the deck; 0 if the yarns do not
            converge on one.
        fell_radius: Radius of the fell, 0 for a braiding point; None if the
            yarns do not converge.
        axis: The braid's axis, in the deck plane.
        contraction: How far the braid itself is drawn in, away from the fell.
        n_formed: Points per yarn above the fell; all of them if None.
        yarn_diameter: The yarn's thickness, if the braid was made for one;
            it is then drawn that thick.
    """

    times: np.ndarray
    points: dict[Hashable, np.ndarray]
    take_off: float
    trajectories: StrandTrajectories
    fell_height: float = 0.0
    fell_radius: float | None = None
    axis: tuple[float, float] = (0.0, 0.0)
    contraction: float = 1.0
    n_formed: int | None = None
    yarn_diameter: float | None = None

    @property
    def length(self) -> float:
        """How much braid has come off, measured above the fell."""
        n = self.formed_count
        return float(self.take_off * (self.times[n - 1] - self.times[0]))

    @property
    def top(self) -> float:
        """Height of the oldest yarn."""
        return self.fell_height + self.length

    @property
    def formed_count(self) -> int:
        """Points per yarn in the braid itself, above the fell.

        They come first; any after them run down from the fell to the carrier.
        """
        return len(self.times) if self.n_formed is None else self.n_formed

    def formed(self) -> np.ndarray:
        """The braid above the fell, one row per yarn; shape ``(yarns, n, 3)``.

        Every yarn is sampled at the same heights, so ``[:, i]`` is one level.
        """
        n = self.formed_count
        return np.stack([pts[:n] for pts in self.points.values()])

    def closest_approach(self, include_fell: bool = True) -> float:
        """The nearest two different yarns come in the braid, over its samples.

        Args:
            include_fell: Count the fell itself.  At a braiding point every
                yarn meets there, so the answer is 0 unless it is left out.
        """
        formed = self.formed()
        if not include_fell:
            formed = formed[:, :-1]
        return _closest_approach(formed, self._level_spacing())

    def _level_spacing(self) -> float:
        n = self.formed_count
        return self.take_off * float(self.times[1] - self.times[0]) if n > 1 else 0.0

    def to_parametric_braid(self):
        """The same yarns as a :class:`~braidpy.parametric_braid.ParametricBraid`.

        Each strand is parametrised from the deck (0) to the oldest yarn (1),
        and interpolated linearly between samples, so the drawing and the
        measuring done on parametric braids apply here too.

        Returns:
            ParametricBraid: One strand per yarn, in order.
        """
        from braidpy.parametric_braid import ParametricBraid
        from braidpy.parametric_strand import ParametricStrand

        def strand(points: np.ndarray) -> ParametricStrand:
            path = points[::-1]
            s = np.linspace(0.0, 1.0, len(path))

            def func(u: float) -> tuple[float, float, float]:
                x, y, z = (float(np.interp(u, s, path[:, i])) for i in range(3))
                return x, y, z

            return ParametricStrand(func)

        return ParametricBraid([strand(self.points[cid]) for cid in self.points])
