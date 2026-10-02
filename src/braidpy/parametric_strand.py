import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

from braidpy.utils import StrictlyPositiveInt


# Type alias for an arc of a strand: a time interval and a 3D path function over that interval
Arc = Tuple[float, float, Callable[[float], Tuple[float, float, float]]]


def make_arc(
    x_start: float, x_end: float, t_start: float, t_end: float, amplitude: float
) -> Callable[[float], Tuple[float, float, float]]:
    """
    Creates a sine-arc parametric function between two x-positions.

    Args:
        x_start(float): Starting x position.
        x_end(float): Ending x position.
        t_start(float): Start time.
        t_end(float): End time.
        amplitude(float): Amplitude of the sine wave in the y-direction.

    Returns:
        A function that maps time t to a 3D point (x, y, z).
    """

    def arc(t: float) -> Tuple[float, float, float]:
        progress = (t - t_start) / (t_end - t_start)
        x = x_start + (x_end - x_start) * progress
        y = amplitude * math.sin(math.pi * progress)
        return x, y, t

    return arc


def make_idle_arc(
    x: float, t_start: float, t_end: float
) -> Callable[[float], Tuple[float, float, float]]:
    """
    Creates a straight-line parametric function for idle strands.

    Args:
        x: Fixed x position.
        t_start: Start time.
        t_end: End time.

    Returns:
        A function that maps time t to a 3D point (x, 0.0, z).
    """

    def arc(t: float) -> Tuple[float, float, float]:
        return x, 0.0, t

    return arc


def combine_arcs(arcs: List[Arc]) -> Callable[[float], Tuple[float, float, float]]:
    """
    Combines a list of arcs into a single time-dependent function.

    Args:
        arcs: A list of arcs represented as (t_start, t_end, function).

    Returns:
        A function from t to (x, y, z), switching arcs over time.
    """

    def strand_func(t: float) -> Tuple[float, float, float]:
        for t0, t1, arc in arcs:
            if t0 <= t <= t1:
                return arc(t)
        raise ValueError(f"Time {t} is out of bounds for this strand.")

    return strand_func


class ParametricStrand:
    def __init__(self, func: Callable[[float], tuple]) -> None:
        """

        Args:
            func(Callable[[float], tuple]): a function γ(t) : [0,1] → ℝ³
        """
        self.func = func

    def evaluate(self, t: float) -> tuple[float, float, float]:
        """
        Compute the strand position at time t (along z axis)
        Args:
            t: time or z coordinates

        Returns:
            tuple[float, float, float]: position of braid [x(t), y(t), t]
        """
        if t < 0 or t > 1:
            raise ValueError("t must be in [0, 1]")
        return self.func(t)

    def sample(self, n: StrictlyPositiveInt = 100) -> List[tuple]:
        """
        Return a list of sampled points for plotting

        Args:
            n(StrictlyPositiveInt): number of samples

        Returns:
            List[tuple]: list of 3D coordinates
        """
        return [self.evaluate(i / (n - 1)) for i in range(n)]


# ── A braided strand, written down rather than sampled ────────────────────────
#
# `make_arc` above builds one segment at a time and hands back a closure.
# What follows keeps the same geometry in a form that can be reasoned about:
# the slots a strand passes through, which side of each crossing it took, and
# the shape it uses to travel between slots.  That is enough to write its
# Fourier series exactly (see braidpy.harmonic_strand) instead of sampling it.
#
# It is a *drawing* convention, the same one `make_arc` implements, and not
# the shape a strand takes under tension.  See src/braidpy/analytic for why
# there is no closed form for the latter.

# A transition profile as polynomial coefficients in the segment parameter
# tau, lowest power first: P(tau) = c0 + c1 tau + c2 tau^2 + ...
Profile = Tuple[float, ...]

#: Straight from slot to slot, which is what `make_arc` does.
LINEAR: Profile = (0.0, 1.0)

#: The cubic 3 tau^2 - 2 tau^3.  Among transitions that leave and arrive
#: parallel to the axis it is the one that minimises bending energy, so a
#: strand drawn with it has no corner where a crossing begins or ends.
SMOOTHSTEP: Profile = (0.0, 0.0, 3.0, -2.0)


def evaluate_profile(profile: Profile, tau: float) -> float:
    """The profile at ``tau``, by Horner's rule.

    Args:
        profile: Polynomial coefficients, lowest power first.
        tau: Position within the segment, 0 to 1.

    Returns:
        P(tau), which is 0 at the start of a segment and 1 at the end.
    """
    value = 0.0
    for coefficient in reversed(profile):
        value = value * tau + coefficient
    return value


@dataclass(frozen=True)
class StrandPath:
    """One strand's path through a braid, segment by segment.

    Unlike :class:`ParametricStrand`, which is a closure, this keeps the
    braid's own description of the strand — where it is and what it passed —
    so that exact things can be computed from it.  One unit of ``z`` per
    generator, and it repeats.

    Args:
        slots: The slot it occupies at each of ``len(signs) + 1`` instants.
        signs: Per segment, +1 if it crosses over, -1 if under, 0 if it holds
            its slot.
        spacing: Distance between neighbouring slots.
        amplitude: How far off the axis a crossing strand rides.
        profile: How it travels sideways; see :data:`LINEAR` and
            :data:`SMOOTHSTEP`.
    """

    slots: Tuple[int, ...]
    signs: Tuple[int, ...]
    spacing: float = 1.0
    amplitude: float = 0.2
    profile: Profile = LINEAR

    @property
    def length(self) -> int:
        """The braid's period along its axis, one unit per generator."""
        return len(self.signs)

    def position(self, z: float) -> Tuple[float, float, float]:
        """Where the strand is at ``z`` along the axis.

        ``z`` is taken modulo the period, so a closed braid can be followed
        round as many times as wanted.

        Args:
            z: Distance along the braid axis.

        Returns:
            (x, y, z) — sideways, off-axis, and along.
        """
        segment = int(math.floor(z)) % self.length
        tau = z - math.floor(z)

        start = self.slots[segment] * self.spacing
        end = self.slots[segment + 1] * self.spacing
        x = start + (end - start) * evaluate_profile(self.profile, tau)
        y = self.signs[segment] * self.amplitude * math.sin(math.pi * tau)
        return x, y, z

    def to_parametric(self) -> "ParametricStrand":
        """The same path as a :class:`ParametricStrand`, on t in [0, 1].

        So that everything already built on parametric strands — sampling,
        :class:`~braidpy.parametric_braid.ParametricBraid` and its plotting —
        works on this without knowing what it is.
        """
        return ParametricStrand(lambda t: self.position(t * self.length))


def strand_paths(
    braid,
    spacing: float = 1.0,
    amplitude: float = 0.2,
    profile: Profile = LINEAR,
) -> List[StrandPath]:
    """The path of every strand of a braid.

    Which strand of a crossing goes over is read from the generator's sign,
    not from the direction it moves: a positive generator sends the strand
    coming from the lower slot over the top, and its inverse sends the one
    from the upper slot over instead.  Both exchange the same pair, so a
    model that watched only the slots would make a braid and its inverse
    identical.

    Args:
        braid: A :class:`~braidpy.braid.Braid`.
        spacing: Distance between neighbouring slots.
        amplitude: How far off the axis a crossing strand rides.
        profile: How a strand travels sideways within a segment.

    Returns:
        One :class:`StrandPath` per strand, in strand order.
    """
    generators = list(braid.generators)
    n_strands = braid.n_strands or max(abs(g) for g in generators) + 1
    history = braid.slot_history()

    paths = []
    for strand in range(n_strands):
        slots = tuple(row[strand] for row in history)
        signs = []
        for segment, generator in enumerate(generators):
            here = slots[segment]
            if not generator or here == slots[segment + 1]:
                signs.append(0)
                continue
            lower = abs(generator) - 1
            over = (here == lower and generator > 0) or (
                here == lower + 1 and generator < 0
            )
            signs.append(1 if over else -1)
        paths.append(
            StrandPath(
                slots=slots,
                signs=tuple(signs),
                spacing=spacing,
                amplitude=amplitude,
                profile=profile,
            )
        )
    return paths


def arc_length(strand, n_samples: int = 4000) -> float:
    """How long a strand is over a period, measured along the strand.

    Compare it with the strand's ``length``, which is the distance the same
    period covers along the axis: the difference is what the braid costs in
    yarn over running straight.  Works on anything that answers
    ``position(z)`` — a path, a series, a helix.

    Args:
        strand: The strand to measure.
        n_samples: Segments to measure along.  A sum of chords always
            understates a curve, so this converges from below.

    Returns:
        The length of one period.
    """
    total = 0.0
    previous = strand.position(0.0)
    for sample in range(1, n_samples + 1):
        here = strand.position(strand.length * sample / n_samples)
        total += math.dist(previous, here)
        previous = here
    return total


def transported_frame(points):
    """A frame carried along a centreline without spinning about it.

    Two vectors square to the curve and to each other at every point, got by
    rolling the previous pair onto the new tangent — parallel transport.  The
    obvious alternatives both misbehave:

    - the Frenet frame flips at an inflection, where the curve straightens
      and the normal is undefined, which creases a tube drawn on it;
    - recomputing a frame at each point from a fixed world axis, as the
      Cosserat animation's ``create_circle`` does, leaves consecutive rings
      unaligned, so a tube built segment by segment does not join up — and
      it degenerates when the curve runs along that axis, which
      ``np.allclose(direction, [0, 0, 1])`` catches going up and misses
      coming down.

    The carried frame need not close up after a loop.  For a tube of
    circular section in one colour that is invisible; for anything painted
    round the tube it is not.

    Args:
        points: The centreline, as a sequence of (x, y, z).

    Returns:
        (centre, normal, binormal) as arrays of one row per point.
    """
    import numpy as np

    centre = np.asarray(points, dtype=float)

    # Tangents by central differences, so a sample is not biased forwards.
    ahead = np.roll(centre, -1, axis=0)
    behind = np.roll(centre, 1, axis=0)
    ahead[-1] = centre[-1] + (centre[-1] - centre[-2])
    behind[0] = centre[0] - (centre[1] - centre[0])
    tangents = ahead - behind
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]

    # A first normal, any direction square to the tangent.
    seed = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(seed, tangents[0]))) > 0.9:
        seed = np.array([1.0, 0.0, 0.0])
    normal = np.cross(tangents[0], seed)
    normal /= np.linalg.norm(normal)

    normals = [normal]
    for step in range(1, len(tangents)):
        before, after = tangents[step - 1], tangents[step]
        axis = np.cross(before, after)
        sine = float(np.linalg.norm(axis))
        if sine < 1e-12:
            normals.append(normals[-1])
            continue
        axis = axis / sine
        angle = math.atan2(sine, float(np.dot(before, after)))
        # Rodrigues: roll the previous normal onto the new tangent's plane.
        carried = (
            normals[-1] * math.cos(angle)
            + np.cross(axis, normals[-1]) * math.sin(angle)
            + axis * float(np.dot(axis, normals[-1])) * (1.0 - math.cos(angle))
        )
        normals.append(carried / np.linalg.norm(carried))

    normals = np.array(normals)
    return centre, normals, np.cross(tangents, normals)


def tube_rings(points, radius: float, n_around: int = 16):
    """A ring of points round the centreline at every sample.

    The shared half of drawing a strand as yarn: :func:`tube_mesh` reshapes
    this for a surface plot and :func:`tube_faces` stitches it into quads,
    so the two renderings cannot drift apart.

    Args:
        points: The centreline, as a sequence of (x, y, z).
        radius: The tube's radius, which is half the strand's diameter.
        n_around: Points round the circle.

    Returns:
        An ``(len(points), n_around + 1, 3)`` array.  The ring is closed: its
        first point is repeated at the end.
    """
    import numpy as np

    centre, normals, binormals = transported_frame(points)
    around = np.linspace(0.0, 2.0 * math.pi, n_around + 1)
    ring = (
        radius * np.cos(around)[None, :, None] * normals[:, None, :]
        + radius * np.sin(around)[None, :, None] * binormals[:, None, :]
    )
    return centre[:, None, :] + ring


def tube_mesh(points, radius: float, n_around: int = 16):
    """A strand drawn as what it is: a tube of yarn, not a line.

    Sweeps a circle of ``radius`` along a sampled centreline, so a picture of
    a braid shows its strands at their real thickness — and therefore shows
    them touching, which is the whole of what sets a braid's size.  A line
    drawing cannot show that and has to be believed instead.

    Takes the points rather than a strand, so it serves anything that can be
    sampled: a :class:`ParametricStrand` via :meth:`~ParametricStrand.sample`,
    a :class:`StrandPath`, a helix, or a rod simulation's output.

    Args:
        points: The centreline, as a sequence of (x, y, z).
        radius: The tube's radius, which is half the strand's diameter.
        n_around: Points round the circle.

    Returns:
        (x, y, z), each a ``(len(points), n_around + 1)`` array, ready for a
        surface plot.
    """
    surface = tube_rings(points, radius, n_around)
    return surface[:, :, 0], surface[:, :, 1], surface[:, :, 2]


def tube_faces(points, radius: float, n_around: int = 16, stride: int = 1):
    """The same tube as quads, for a renderer that wants polygons.

    Matplotlib's ``Poly3DCollection`` takes faces rather than a surface, so
    this is what to hand it — and because it shares
    :func:`tube_rings` with :func:`tube_mesh`, the matplotlib and Plotly
    pictures are of the same tube.

    Args:
        points: The centreline, as a sequence of (x, y, z).
        radius: The tube's radius.
        n_around: Points round the circle.
        stride: Take every n-th sample along the centreline, for an animation
            that has to redraw quickly.

    Returns:
        A list of four-cornered faces, each a list of (x, y, z).
    """
    rings = tube_rings(points, radius, n_around)[::stride]
    return [
        [
            rings[along, step],
            rings[along, step + 1],
            rings[along + 1, step + 1],
            rings[along + 1, step],
        ]
        for along in range(len(rings) - 1)
        for step in range(rings.shape[1] - 1)
    ]
