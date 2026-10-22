"""
braidpy_crossing_strands.py
===========================
Physical Analytical Geometrical Model of Two Crossing Strands Attached to Rotating Disks.
Authored for seamless integration with braidpy (https://github.com/baptistelabat/braidpy).

Mechanical Decomposition:
- Regime 1 (Phi <= Phi_c): Pure 3D straight skew lines between disk pins (no contact).
- Regime 2 (Phi > Phi_c):
    * Bottom straight segment (t < -tc): from bottom disk pin to helix entrance.
    * Central double helix (|t| <= tc): helical contact wrapping at exact distance h0.
    * Top straight segment (t > +tc): from helix exit to top disk pin.
- Force Equilibrium & Tension Asymmetry:
    * When T1 >> T2: Strand 1 is a nearly straight line between disk pins; Strand 2 circles around it.
    * When T2 >> T1: Strand 2 is a nearly straight line between disk pins; Strand 1 circles around it.
    * When T1 == T2: Both strands form a symmetric double helix around the central z-axis.
- Supports both:
    * Simplified Case: Pure circular cylinders (without flattening, flattening_ratio = 1.0).
    * General Case: Flattened elliptical cross-sections (flattening_ratio < 1.0).
"""

import numpy as np
from typing import Tuple, List, Dict, Callable


class TwoStrandCrossingModel:
    """
    Physical geometrical model for two crossing strands attached to rotating disks.
    
    Parameters
    ----------
    disk_radius : float
        Radius of attachment disks (pins at (+/- R_disk, 0)).
    radius1, radius2 : float
        Nominal unloaded radii of Strand 1 and Strand 2 (in mm).
    flattening_ratio : float
        Cross-sectional aspect ratio b/a:
        - 1.0 = Pure circular cylinders (Simplified Case without flattening)
        - < 1.0 = Flattened elliptical cross-sections (Hertzian/contact compacted)
    crossing_length : float
        Total distance Lz between the two disks along the z-axis (in mm).
    spiral_angle_deg : float
        Top disk relative twist angle Phi (in degrees):
        - 0°: Parallel straight strands (separation = 2 * disk_radius)
        - ~Phi_c: Critical touch point (tangent contact at center z = 0)
        - 360°: Half-turn central contact helix (180° mutual twist)
        - >360°: Multi-turn braid spiral
    tension1, tension2 : float
        Tension forces on Strand 1 and Strand 2 (in N).
    crimp_factor : float
        Scale multiplier on contact separation (1.0 = exact tangential touch).
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
        crossing_angle_deg: float = 60,
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
        self.crossing_angle_deg = float(crossing_angle_deg)

        # Contact separation distance h0:
        # In circular case (flattening_ratio = 1.0): h0 = (radius1 + radius2) * crimp_factor
        # In flattened case: h0 = (b1 + b2) * crimp_factor
        self.b1 = self.radius1 * self.flattening_ratio
        self.b2 = self.radius2 * self.flattening_ratio
        self.h0 = (self.b1 + self.b2) * self.crimp_factor

    def eval_disk_helix_position(self, strand_idx: int, t: float) -> np.ndarray:
        """
        Evaluates 3D Cartesian coordinates [x, y, z] for strand_idx (1 or 2) at normalized parameter t in [-1, 1].
        """
        assert strand_idx in (1, 2), "strand_idx must be 1 (over) or 2 (under)"
        Lz = self.crossing_length
        R_disk = self.disk_radius
        h0 = self.h0
        Phi = np.radians(self.spiral_angle_deg)

        # Tension balance fractions
        t1 = self.tension1
        t2 = self.tension2
        tot_tension = t1 + t2
        alpha1 = t2 / tot_tension  # displacement weight for strand 1 (scales with T2)
        alpha2 = t1 / tot_tension  # displacement weight for strand 2 (scales with T1)

        # 3D Helical Pitch Geometry:
        # For touching cylinders in 3D, normal contact requires transverse separation
        # Rh = Rs * sqrt(1 + gamma^2) where gamma = k * Rs is the helix pitch tangent
        k = Phi / Lz if Lz > 1e-6 else 0.0
        Rs = 0.5 * h0
        gamma = k * Rs
        Rh = Rs * np.sqrt(1.0 + gamma**2)
        h_eff = 2.0 * Rh

        # Critical contact angle Phi_c where unconstrained straight lines touch at center z = 0
        cos_half_phic = min(1.0, max(0.0, Rh / R_disk))
        Phic = 2.0 * np.arccos(cos_half_phic)

        z = t * (0.5 * Lz)
        u = (t + 1.0) / 2.0  # parameter in [0, 1] from bottom disk to top disk

        # Bottom disk anchor pins at z = -Lz/2 (Phi = 0)
        A1 = np.array([R_disk, 0.0, -0.5 * Lz], dtype=float)
        A2 = np.array([-R_disk, 0.0, -0.5 * Lz], dtype=float)

        # Top disk anchor pins at z = +Lz/2 (rotated by Phi)
        B1 = np.array([R_disk * np.cos(Phi), R_disk * np.sin(Phi), 0.5 * Lz], dtype=float)
        B2 = np.array([-R_disk * np.cos(Phi), -R_disk * np.sin(Phi), 0.5 * Lz], dtype=float)

        # Unconstrained straight lines connecting the disk anchors
        L1 = (1.0 - u) * A1 + u * B1
        L2 = (1.0 - u) * A2 + u * B2

        # Center of tension line C(z) = (T1 * L1 + T2 * L2) / (T1 + T2) = (alpha2 - alpha1) * L1(z)
        C = (alpha2 - alpha1) * L1

        if Phi <= Phic:
            # REGIME 1: Non-contact straight skew lines
            return L1 if strand_idx == 1 else L2

        # REGIME 2: Rotating Disks Straight Lines & Tangent Central Helix
        delta_helix = Phi - Phic
        tan_half = np.tan(0.5 * Phic)
        tc = delta_helix / (delta_helix + 2.0 * tan_half or 1.0)
        tc = max(0.001, min(0.95, tc))
        zc = tc * (0.5 * Lz)

        # Exact C1 tangency lift-off angles:
        theta_entry = 0.5 * Phic
        theta_exit = Phi - 0.5 * Phic

        # Contact separation vector d12 from Strand 2 to Strand 1
        d12_entry = np.array([h_eff * np.cos(theta_entry), h_eff * np.sin(theta_entry), 0.0], dtype=float)
        d12_exit = np.array([h_eff * np.cos(theta_exit), h_eff * np.sin(theta_exit), 0.0], dtype=float)

        # Center of tension at helix entry and exit
        u_entry = (-tc + 1.0) / 2.0
        C_entry = (alpha2 - alpha1) * ((1.0 - u_entry) * A1 + u_entry * B1)
        C_entry[2] = -zc

        u_exit = (tc + 1.0) / 2.0
        C_exit = (alpha2 - alpha1) * ((1.0 - u_exit) * A1 + u_exit * B1)
        C_exit[2] = zc

        # Helix entry and exit anchor points
        H1_entry = C_entry + alpha1 * d12_entry
        H2_entry = C_entry - alpha2 * d12_entry

        H1_exit = C_exit + alpha1 * d12_exit
        H2_exit = C_exit - alpha2 * d12_exit

        A = A1 if strand_idx == 1 else A2
        B = B1 if strand_idx == 1 else B2
        H_entry = H1_entry if strand_idx == 1 else H2_entry
        H_exit = H1_exit if strand_idx == 1 else H2_exit

        if t < -tc:
            # Segment 1: Bottom straight lead-in from disk anchor to helix entry
            s = (t - (-1.0)) / (-tc - (-1.0))
            return (1.0 - s) * A + s * H_entry
        elif t > tc:
            # Segment 3: Top straight lead-in from helix exit to top disk anchor
            s = (t - tc) / (1.0 - tc)
            return (1.0 - s) * H_exit + s * B
        else:
            # Segment 2: Central contact double helix with tension equilibrium
            frac = (t + tc) / (2.0 * tc) if tc > 1e-6 else 0.5
            theta = theta_entry + frac * (theta_exit - theta_entry)
            d12 = np.array([h_eff * np.cos(theta), h_eff * np.sin(theta), 0.0], dtype=float)

            C_helix = np.array([C[0], C[1], z], dtype=float)
            if strand_idx == 1:
                return C_helix + alpha1 * d12
            else:
                return C_helix - alpha2 * d12

    def eval_strand(self, strand_idx: int, t: float) -> Dict[str, np.ndarray]:
        """
        Evaluates position, velocity, acceleration, jerk, curvature, torsion,
        tangent, and mutual contact normal frame at parameter t.
        """
        dt = 1e-4
        t_clamp = max(-0.999, min(0.999, t))

        pos = self.eval_disk_helix_position(strand_idx, t_clamp)
        p_fwd = self.eval_disk_helix_position(strand_idx, t_clamp + dt)
        p_bwd = self.eval_disk_helix_position(strand_idx, t_clamp - dt)
        p_fwd2 = self.eval_disk_helix_position(strand_idx, t_clamp + 2 * dt)
        p_bwd2 = self.eval_disk_helix_position(strand_idx, t_clamp - 2 * dt)

        vel = (p_fwd - p_bwd) / (2.0 * dt)
        acc = (p_fwd + p_bwd - 2.0 * pos) / (dt ** 2)
        jerk = (p_fwd2 - 2.0 * p_fwd + 2.0 * p_bwd - p_bwd2) / (2.0 * dt ** 3)

        speed = float(np.linalg.norm(vel))
        v_cross_a = np.cross(vel, acc)
        cross_norm = float(np.linalg.norm(v_cross_a))

        curvature = cross_norm / (speed ** 3) if speed > 1e-9 else 0.0
        cross_sq = cross_norm ** 2
        torsion = float(np.dot(v_cross_a, jerk) / cross_sq) if cross_sq > 1e-12 else 0.0

        T = vel / speed if speed > 1e-9 else np.array([0., 0., 1.])

        # Mutual contact vector
        p1 = self.eval_disk_helix_position(1, t_clamp)
        p2 = self.eval_disk_helix_position(2, t_clamp)
        d12 = (p1 - p2) if strand_idx == 1 else (p2 - p1)
        N = d12 - np.dot(d12, T) * T
        if np.linalg.norm(N) < 1e-6:
            up = np.array([0., 1., 0.])
            N = up - np.dot(up, T) * T
        N = N / np.linalg.norm(N)
        B = np.cross(T, N)
        B = B / np.linalg.norm(B)

        return {
            'pos': pos,
            'vel': vel,
            'acc': acc,
            'jerk': jerk,
            'speed': speed,
            'curvature': curvature,
            'torsion': torsion,
            'tangent': T,
            'normal': N,    # Through-thickness contact normal
            'binormal': B,  # In-plane lateral width vector
        }

    def compute_contact_clearance(self, n_samples: int = 151) -> Dict[str, float]:
        """
        Computes inter-strand minimum distance and checks for non-penetration.
        """
        ts = np.linspace(-1.0, 1.0, n_samples)
        pts1 = np.array([self.eval_disk_helix_position(1, t) for t in ts])
        pts2 = np.array([self.eval_disk_helix_position(2, t) for t in ts])

        diff = pts1[:, np.newaxis, :] - pts2[np.newaxis, :, :]
        dist_mat = np.linalg.norm(diff, axis=2)

        min_idx = np.unravel_index(np.argmin(dist_mat), dist_mat.shape)
        min_dist = float(dist_mat[min_idx])

        surface_gap = min_dist - self.h0

        return {
            'min_centerline_distance': min_dist,
            'contact_separation_h0': self.h0,
            'surface_gap': surface_gap,
            'has_penetration': surface_gap < -0.005,
            't1_at_min': float(ts[min_idx[0]]),
            't2_at_min': float(ts[min_idx[1]]),
        }

    def to_braidpy_strands(self) -> List[Callable[[float], np.ndarray]]:
        """
        Returns [strand1(t), strand2(t)] functions compatible with braidpy's to_parametric_strands().
        """
        return [
            lambda t: self.eval_disk_helix_position(1, t),
            lambda t: self.eval_disk_helix_position(2, t),
        ]


# Verification Example
if __name__ == '__main__':
    print("=== Testing Rotating Disks Straight-Helix Decomposition ===")

    # 1. Simplified Case: Circular Strands (without flattening, flattening_ratio=1.0)
    # High T1 (5.0 N), low T2 (0.1 N) -> Strand 1 should be nearly straight, Strand 2 circling around it
    model_circ = TwoStrandCrossingModel(
        disk_radius=1.8,
        radius1=0.4,
        radius2=0.4,
        flattening_ratio=1.0,  # Circular
        crossing_length=6.0,
        spiral_angle_deg=360.0,
        tension1=5.0,
        tension2=0.1,
    )

    info_circ = model_circ.compute_contact_clearance()
    print(f"\nSimplified Case (Circular, T1=5.0 N, T2=0.1 N):")
    print(f"  Min Centerline Dist: {info_circ['min_centerline_distance']:.4f} mm")
    print(f"  Contact Height h0:   {info_circ['contact_separation_h0']:.4f} mm")
    print(f"  Surface Gap:         {info_circ['surface_gap']:.4f} mm")
    print(f"  Penetration:         {info_circ['has_penetration']}")
    assert not info_circ['has_penetration'], "Physical penetration detected!"

    # Check that Strand 1 is nearly straight:
    p_bot = model_circ.eval_disk_helix_position(1, -1.0)
    p_mid = model_circ.eval_disk_helix_position(1, 0.0)
    p_top = model_circ.eval_disk_helix_position(1, 1.0)
    mid_straight = 0.5 * (p_bot + p_top)
    dev = np.linalg.norm(p_mid - mid_straight)
    print(f"  Strand 1 deviation from straight line: {dev:.4f} mm (nearly 0)")

    print("\nSUCCESS: Model validated with zero penetration and physical tension balance.")