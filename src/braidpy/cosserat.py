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
radius = 0.2
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
lines = [ax.plot([], [], [], lw=2)[0] for _ in range(n_rods)]

# Set axis limits
ax.set_xlim(-0.5, 3.5)
ax.set_ylim(-1.0, 2.0)
ax.set_zlim(-1.0, 1.5)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Polyline Rod Simulation")


def init():
    for line in lines:
        line.set_data([], [])
        line.set_3d_properties([])
    return lines


def update(frame_idx):
    for i, line in enumerate(lines):
        pos = frames_per_rod[i][frame_idx]
        line.set_data(pos[0], pos[1])
        line.set_3d_properties(pos[2])
    return lines


ani = animation.FuncAnimation(
    fig, update, frames=n_frames, init_func=init, blit=True, interval=40
)

# To save animation to file
ani.save("polyline_rod_animation.mp4", fps=25, bitrate=1800)

plt.show()
