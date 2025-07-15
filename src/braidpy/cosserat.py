import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict
from elastica import (
    BaseSystemCollection,
    Constraints,
    Connections,
    Forcing,
    Damping,
    CallBacks,
    CosseratRod,
    OneEndFixedBC,
    AnalyticalLinearDamper,
    PositionVerlet,
    integrate,
    CallBackBaseClass,
    GravityForces,
    RodRodContact,
    Contact,
)

from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class TimedPointPin(CallBackBaseClass):
    """
    Pins a point at a fixed position until a given release time,
    after which the point is free to move.
    """

    def __init__(self, idx, pin_position, release_time: float):
        super().__init__()
        self.idx = idx
        self.pin_position = np.array(pin_position)
        self.release_time = release_time
        self.released = False

    def make_callback(self, system, time, current_step: int):
        if not self.released and time < self.release_time:
            # Pin the point
            system.position_collection[..., self.idx] = self.pin_position
            system.velocity_collection[..., self.idx] = 0.0
        elif time >= self.release_time and not self.released:
            # Mark as released
            print(f"⏱️ Releasing point at time {time:.3f}")
            self.released = True


# ---- Simulation Setup ---- #


class PolylineRodSimulator(
    BaseSystemCollection, Constraints, Connections, Forcing, Damping, CallBacks, Contact
):
    pass


sim = PolylineRodSimulator()

# Define polyline points
points = [
    np.array([0.0, 0.0, 0.0]),
    np.array([0.5, 0.5, 2.0]),
    np.array([2.0, 1.0, 0.0]),
]

end_points = [
    np.array([1.0, 0.5, 2.0]),
    np.array([1.0, -0.5, 2.0]),
    np.array([3.0, 1.0, 0.5]),
]

n_elements = 20
radius = 0.1
density = 1000
E = 1e6
poisson_ratio = 0.5
shear_modulus = E / (2 * (1 + poisson_ratio))

rods = []

# Create rods between polyline points
for i in range(len(points)):
    start = points[i]
    end = end_points[i]
    direction = end - start
    length = np.linalg.norm(direction)
    direction /= length

    if np.allclose(direction, [0, 0, 1]):
        normal = np.array([1.0, 0.0, 0.0])
    else:
        normal = np.cross(direction, [0, 0, 1])
        normal /= np.linalg.norm(normal)

    rod = CosseratRod.straight_rod(
        n_elements=n_elements,
        start=start,
        direction=direction,
        normal=normal,
        base_length=length,
        base_radius=radius,
        density=density,
        youngs_modulus=E,
        shear_modulus=shear_modulus,
    )

    sim.append(rod)
    rods.append(rod)

# # Connect rods
# for i in range(len(rods) - 1):
#     sim.connect(rods[i], rods[i + 1], first_connect_idx=-1, second_connect_idx=0).using(
#         FreeJoint, k=1e5, nu=1e2
#     )

# Fix first end
sim.constrain(rods[0]).using(
    OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
)
# Fix first end
# sim.constrain(rods[1]).using(
#     OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
# )

# Fix first end
sim.constrain(rods[2]).using(
    OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
)

sim.collect_diagnostics(rods[0]).using(
    TimedPointPin,
    idx=10,
    pin_position=[0.5, 0.25, 0.0],
    release_time=1.5,  # seconds
)

# Add forces and damping
for rod in rods:
    sim.add_forcing_to(rod).using(
        GravityForces, acc_gravity=np.array([0.0, 0.0, -9.81])
    )
    sim.dampen(rod).using(AnalyticalLinearDamper, damping_constant=1, time_step=1e-4)

sim.detect_contact_between(rods[0], rods[1]).using(RodRodContact, k=1e3, nu=10.0)

# ---- Diagnostics ---- #


class GlobalCallBack(CallBackBaseClass):
    def __init__(self, step_skip: int, callback_params: dict):
        super().__init__()
        self.every = step_skip
        self.callback_params = callback_params

    def make_callback(self, system, time, current_step: int):
        if current_step % self.every == 0:
            if "frames" not in self.callback_params:
                self.callback_params["frames"] = []
            self.callback_params["frames"].append(system.position_collection.copy())


pp_list = defaultdict(list)
for rod in rods:
    sim.collect_diagnostics(rod).using(
        GlobalCallBack, step_skip=200, callback_params=pp_list
    )

# ---- Finalize and Run ---- #

sim.finalize()
final_time = 5.0
dt = 1e-4
total_steps = int(final_time / dt)
integrate(PositionVerlet(), sim, final_time, total_steps)

# ---- Animation ---- #

frames = np.array(pp_list["frames"])  # [n_frames, 3, n_nodes]
n_rods = len(rods)
n_frames = len(frames) // n_rods
frames_per_rod = [frames[i::n_rods] for i in range(n_rods)]

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim(-0.5, 3.5)
ax.set_ylim(-1.0, 2.0)
ax.set_zlim(-1.0, 1.5)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Rod Visualization with Tube Geometry")

# Each rod will have a list of Poly3DCollections
tube_patches = []
colors = [
    "red",
    "green",
    "blue",
    "skyblue",
    "orange",
    "limegreen",
    "crimson",
    "purple",
    "gold",
]

for i, _ in enumerate(rods):
    tube = Poly3DCollection([], alpha=0.7, color=colors[i % len(colors)])

    ax.add_collection3d(tube)
    tube_patches.append(tube)


# ---- Tube Rendering Animation ---- #


def create_circle(center, direction, radius, resolution=8):
    """Create circle points perpendicular to direction."""
    direction = direction / np.linalg.norm(direction)
    if np.allclose(direction, [0, 0, 1]):
        ortho1 = np.array([1, 0, 0])
    else:
        ortho1 = np.cross(direction, [0, 0, 1])
        ortho1 /= np.linalg.norm(ortho1)
    ortho2 = np.cross(direction, ortho1)

    angles = np.linspace(0, 2 * np.pi, resolution)
    circle = [
        center + radius * (np.cos(a) * ortho1 + np.sin(a) * ortho2) for a in angles
    ]
    return circle


subsample_stride = 2


def update_tube(frame_idx):
    for i, rod in enumerate(rods):
        pos = frames_per_rod[i][frame_idx]  # [3, n_nodes]
        segments = pos.shape[1] - 1
        faces = []
        for j in range(0, segments, subsample_stride):
            p0 = pos[:, j]
            p1 = pos[:, j + 1]
            direction = p1 - p0
            # Create circles at p0 and p1
            circle0 = create_circle(p0, direction, radius)
            circle1 = create_circle(p1, direction, radius)
            # Create tube quads between corresponding circle points
            for k in range(len(circle0) - 1):
                quad = [circle0[k], circle0[k + 1], circle1[k + 1], circle1[k]]
                faces.append(quad)
        # Close the last quad
        quad = [circle0[-1], circle0[0], circle1[0], circle1[-1]]
        faces.append(quad)

        tube_patches[i].set_verts(faces)
    return tube_patches


ani = animation.FuncAnimation(
    fig, update_tube, frames=n_frames, interval=40, blit=False
)

ani.save("polyline_rod_tubes.mp4", fps=25, bitrate=1800)
plt.show()
