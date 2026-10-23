# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Two strands crossing between two rotating disks.

Each strand is pinned to a bottom disk and a top disk, on opposite sides of
the axis, and the top disk is turned by ``spiral_angle_deg``.  Turned a
little, the strands are two straight skew lines that do not touch.  Past the
critical angle, where the straight lines would touch at mid-height,

    Φc = 2 arccos(h / (2 R_disk)),

with ``h`` their contact distance, they wrap round each other: a straight
lead-in from each bottom pin, a double helix where they touch, and a
straight lead-out to each top pin.

The tensions decide who wraps round whom.  The helix turns round the centre
of tension, ``(T1 L1 + T2 L2) / (T1 + T2)`` where ``L1`` and ``L2`` are the
straight lines between the pins: on the axis for equal tensions, so a
symmetric double helix; on strand 1's straight line when ``T1 ≫ T2``, so
strand 1 stays straight and strand 2 goes round it.

Strands are circular for ``flattening_ratio = 1``; below 1 they are
flattened where they press together, their thickness through the contact
``flattening_ratio`` times their radius, so they come closer.

The shape is drawn, not solved for: straight lines and a helix joined end to
end.  It is then checked, every point of one strand against every point of
the other, and the helix widened until the strands come no closer than their
contact distance anywhere (:meth:`TwoStrandCrossingModel.compute_contact_clearance`).
"""

from __future__ import annotations

from typing import Dict, List, Union

import numpy as np

from braidpy.parametric_strand import ParametricStrand

__all__ = ["TwoStrandCrossingModel"]


class TwoStrandCrossingModel:
    """Two strands crossing between two rotating disks; see the module.

    Lengths are in one unit throughout (millimetres, say), tensions in
    another (newtons).

    Args:
        disk_radius: Where the pins are on each disk: strand 1 at
            ``(+R, 0)``, strand 2 at ``(-R, 0)`` on the bottom disk.
        radius1: Strand 1's radius.
        radius2: Strand 2's radius.
        flattening_ratio: Thickness through the contact over the radius: 1
            for round strands, less for strands flattened against each other.
        crossing_length: Height between the disks.
        spiral_angle_deg: How far the top disk is turned, in degrees: 0 for
            two parallel strands, 360 for a full turn of one round the other.
        tension1: Strand 1's tension; at least 0.01.
        tension2: Strand 2's tension; at least 0.01.
        crimp_factor: Scale on the contact distance; 1 for strands that just
            touch.
    """

    def __init__(
        self,
        disk_radius: float = 1.8,
        radius1: float = 0.4,
        radius2: float = 0.4,
        flattening_ratio: float = 0.75,
        crossing_length: float = 6,
        spiral_angle_deg: float = 180,
        tension1: float = 1,
        tension2: float = 1,
        crimp_factor: float = 1,
    ):
        self.disk_radius = float(disk_radius)
        self.radius1 = float(radius1)
        self.radius2 = float(radius2)
        self.flattening_ratio = float(flattening_ratio)
        self.crossing_length = float(crossing_length)
        self.spiral_angle_deg = max(0.0, float(spiral_angle_deg))
        self.tension1 = max(0.01, float(tension1))
        self.tension2 = max(0.01, float(tension2))
        self.crimp_factor = float(crimp_factor)

        # Thickness of each strand through the contact, and the distance
        # their centres keep where they touch.
        self.b1 = self.radius1 * self.flattening_ratio
        self.b2 = self.radius2 * self.flattening_ratio
        self.h0 = (self.b1 + self.b2) * self.crimp_factor

        # How much the helix is widened beyond its drawn width, so that the
        # strands keep h0 apart at every pair of heights, not only at equal
        # ones: found by _settle.
        self._widening = 1.0
        self._settle()

    def _settle(self, n_samples: int = 201, attempts: int = 30) -> None:
        """Widen the helix until the strands come no closer than ``h0``."""
        for _ in range(attempts):
            nearest = float(
                self.compute_contact_clearance(n_samples)["min_centerline_distance"]
            )
            if nearest >= self.h0 * (1 - 1e-6):
                return
            # A little more than the shortfall, so this ends.
            self._widening *= (self.h0 / nearest) * (1 + 1e-4)

    def eval_disk_helix_position(self, strand_idx: int, t: float) -> np.ndarray:
        """Where a strand is, from its bottom pin, ``t = -1``, to its top pin,
        ``t = 1``.

        Args:
            strand_idx: 1 or 2.
            t: Along the strand, ``-1`` to ``1``, in proportion to height.

        Returns:
            Its centre, ``[x, y, z]``.
        """
        if strand_idx not in (1, 2):
            raise ValueError("strand_idx is 1 or 2.")
        Lz = self.crossing_length
        R_disk = self.disk_radius
        Phi = np.radians(self.spiral_angle_deg)

        # How far each strand is pushed off the centre of tension: the less
        # taut one the more.
        total = self.tension1 + self.tension2
        alpha1 = self.tension2 / total
        alpha2 = self.tension1 / total

        # The distance between the strands where they touch, as drawn: h0,
        # widened where they would otherwise pass closer off level.
        Rh = 0.5 * self.h0 * self._widening
        h_eff = 2.0 * Rh

        # The critical angle, where the straight lines would touch at z = 0.
        Phic = 2.0 * np.arccos(min(1.0, max(0.0, Rh / R_disk)))

        u = (t + 1.0) / 2.0  # 0 at the bottom disk, 1 at the top

        # The pins: bottom disk at z = -Lz/2, top disk turned by Phi.
        A1 = np.array([R_disk, 0.0, -0.5 * Lz])
        A2 = np.array([-R_disk, 0.0, -0.5 * Lz])
        B1 = np.array([R_disk * np.cos(Phi), R_disk * np.sin(Phi), 0.5 * Lz])
        B2 = np.array([-R_disk * np.cos(Phi), -R_disk * np.sin(Phi), 0.5 * Lz])
        A, B = (A1, B1) if strand_idx == 1 else (A2, B2)

        if Phi <= Phic:
            # Turned too little to touch: two straight skew lines.
            return (1.0 - u) * A + u * B

        def on_helix(t: float, theta: float) -> np.ndarray:
            """On the helix at ``t``, turned ``theta``: off the centre of
            tension, (T1 L1 + T2 L2) / (T1 + T2) = (alpha2 - alpha1) L1 in x
            and y as L2 = -L1 there, by the strand's share of the contact
            distance."""
            u = (t + 1.0) / 2.0
            line = (1.0 - u) * A1 + u * B1
            centre = np.array(
                [(alpha2 - alpha1) * line[0], (alpha2 - alpha1) * line[1], t * 0.5 * Lz]
            )
            apart = np.array([h_eff * np.cos(theta), h_eff * np.sin(theta), 0.0])
            return (
                centre + alpha1 * apart if strand_idx == 1 else centre - alpha2 * apart
            )

        # The helix: t from -tc to tc, turning from Phic / 2 to Phi - Phic / 2.
        extra = Phi - Phic
        tc = extra / (extra + (2.0 * np.tan(0.5 * Phic) or 1.0))
        tc = max(0.001, min(0.95, tc))
        theta_entry = 0.5 * Phic
        theta_exit = Phi - 0.5 * Phic

        if t < -tc:
            # Straight, from the bottom pin to where the helix begins.
            s = (t + 1.0) / (1.0 - tc)
            return (1.0 - s) * A + s * on_helix(-tc, theta_entry)
        if t > tc:
            # Straight, from where the helix ends to the top pin.
            s = (t - tc) / (1.0 - tc)
            return (1.0 - s) * on_helix(tc, theta_exit) + s * B
        frac = (t + tc) / (2.0 * tc)
        return on_helix(t, theta_entry + frac * (theta_exit - theta_entry))

    def eval_strand(
        self, strand_idx: int, t: float
    ) -> Dict[str, Union[np.ndarray, float]]:
        """A strand's derivatives and frame at ``t``, by finite differences.

        Args:
            strand_idx: 1 or 2.
            t: Along the strand, ``-1`` to ``1``; kept a little inside, so
                that the differences stay on the strand.

        Returns:
            ``pos``, ``vel``, ``acc``, ``jerk`` (by ``t``), ``speed``,
            ``curvature``, ``torsion``, the unit ``tangent``, ``normal``
            towards the other strand, square to the tangent, and
            ``binormal``.
        """
        dt = 1e-4
        t = max(-0.999, min(0.999, t))
        p_bwd2, p_bwd, pos, p_fwd, p_fwd2 = (
            self.eval_disk_helix_position(strand_idx, t + k * dt)
            for k in (-2, -1, 0, 1, 2)
        )

        vel = (p_fwd - p_bwd) / (2.0 * dt)
        acc = (p_fwd + p_bwd - 2.0 * pos) / dt**2
        jerk = (p_fwd2 - 2.0 * p_fwd + 2.0 * p_bwd - p_bwd2) / (2.0 * dt**3)

        speed = float(np.linalg.norm(vel))
        v_cross_a = np.cross(vel, acc)
        cross_norm = float(np.linalg.norm(v_cross_a))
        curvature = cross_norm / speed**3 if speed > 1e-9 else 0.0
        torsion = (
            float(np.dot(v_cross_a, jerk)) / cross_norm**2 if cross_norm > 1e-6 else 0.0
        )

        tangent = vel / speed if speed > 1e-9 else np.array([0.0, 0.0, 1.0])
        towards = self.eval_disk_helix_position(3 - strand_idx, t) - pos
        normal = towards - np.dot(towards, tangent) * tangent
        if np.linalg.norm(normal) < 1e-6:
            up = np.array([0.0, 1.0, 0.0])
            normal = up - np.dot(up, tangent) * tangent
        normal = normal / np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)

        return {
            "pos": pos,
            "vel": vel,
            "acc": acc,
            "jerk": jerk,
            "speed": speed,
            "curvature": curvature,
            "torsion": torsion,
            "tangent": tangent,
            "normal": normal,
            "binormal": binormal / np.linalg.norm(binormal),
        }

    def compute_contact_clearance(
        self, n_samples: int = 151
    ) -> Dict[str, Union[float, bool]]:
        """How close the strands come: every sampled point of one against
        every sampled point of the other, as strands that wind round each
        other pass closest at different heights.

        Args:
            n_samples: Points along each strand.  A minimum over samples, so
                it comes down as they go up.

        Returns:
            ``min_centerline_distance`` and where, ``t1_at_min`` and
            ``t2_at_min``; ``contact_separation_h0``; ``surface_gap``, the
            first less the second; and ``has_penetration``, whether the gap
            is below -0.005.
        """
        ts = np.linspace(-1.0, 1.0, n_samples)
        pts1 = np.array([self.eval_disk_helix_position(1, t) for t in ts])
        pts2 = np.array([self.eval_disk_helix_position(2, t) for t in ts])
        distances = np.linalg.norm(pts1[:, None, :] - pts2[None, :, :], axis=2)
        i, j = np.unravel_index(np.argmin(distances), distances.shape)
        nearest = float(distances[i, j])
        gap = nearest - self.h0
        return {
            "min_centerline_distance": nearest,
            "contact_separation_h0": self.h0,
            "surface_gap": gap,
            "has_penetration": gap < -0.005,
            "t1_at_min": float(ts[i]),
            "t2_at_min": float(ts[j]),
        }

    def to_parametric_strands(self) -> List[ParametricStrand]:
        """The two strands as braidpy's
        :class:`~braidpy.parametric_strand.ParametricStrand`, over ``[0, 1]``
        from bottom to top, as :meth:`~braidpy.braid.Braid.to_parametric_strands`
        gives a braid's.
        """

        def strand(k: int) -> ParametricStrand:
            return ParametricStrand(
                lambda s: tuple(self.eval_disk_helix_position(k, 2.0 * s - 1.0))
            )

        return [strand(1), strand(2)]
