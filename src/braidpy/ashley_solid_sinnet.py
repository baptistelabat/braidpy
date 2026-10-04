"""Ashley disk braid visualizer.

Renders an annulus partitioned into sectors. Strands in each sector lie on a
common circle and are ordered counterclockwise. Each frame shows the state
before a move, optional arrows for the active move path, and the final state.
Optionally builds an animated GIF.

According to ABOK3036
"All odd strands, when they are moved, are led to the
right, counterclockwise; all even strands are led. to the left, clock-
wise. The earliest strand to occupy any space is always the next one
to be moved from that space. The earliest odd-numbered strand is
always the right-hand strand of its group; when it is moved it is led
to the right, counterclockwise, until it reaches its destination, where
it is put into the near or left-hand position of an odd-numbered
space.
At an even-numbered space the left strand of the group is moved
to the left (clockwise) until it reaches its destination, where it is put
into the right-hand position. The two ways of moving strands are
indicated with arrows in diagram fIi 304 I. All strands are moved
"over alL" If, however, an odd strand is led to an even-numhered
space, as is sometimes the case, it passes to the right as it lea ... ~s the
odd space but is carried to the right side of the even-numbered space
when it arrives. If a strand from an even-numbered space is led to an
odd-numbered space, it is moved to the left but is placed at the left
side of the odd-numbered space."

Requirements:
    matplotlib
    imageio (optional, for GIF)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Dict,
    Hashable,
    List,
    Optional,
    Sequence,
    Tuple,
    cast,
)
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge, FancyArrowPatch, Circle
import matplotlib.cm as cm
from matplotlib.axes import Axes

import imageio.v2 as imageio  # optional for GIF

from braidpy.annulus_braid import solid_word
from braidpy.take_off import disk_annular_word, disk_braid

if TYPE_CHECKING:
    from braidpy.braid import Braid
    from braidpy.mobidai import MobidaiConfig

OFFSET_DEG = 180  # To match Ahsley book of knots
# ============================ Core Structures ============================


@dataclass
class AshleySolidSinnet:
    """Ashley-style braid pattern.

    Spaces are numbered anticlockwise, seen from above, from the left of the
    disk as the book draws it.  A strand is moved over all the strands it
    passes: from an odd space its right-hand strand, anticlockwise; from an
    even space its left-hand strand, clockwise.  It goes in at the left
    (clockwise) end of an odd space and at the right (anticlockwise) end of
    an even one, so the earliest strand in a space is always the next to
    leave it.

    Attributes:
        initial_counts_per_space (List[int]): Number of strands per sector. 1-based sectors.
        moves (List[Tuple[int, int]]): Sequence of (from_sector, to_sector) moves, each 1-based.
    """

    initial_counts_per_space: List[int]
    moves: List[Tuple[int, int]]

    @property
    def n_strands(self) -> int:
        """How many strands the sinnet has."""
        return sum(self.initial_counts_per_space)

    def disk(self, n_cycles: int = 1) -> "SinnetDisk":
        """The sinnet worked on a disk — see :func:`sinnet_disk`."""
        return sinnet_disk(self, n_cycles)

    def annular_word(self, n_cycles: int = 1) -> List[int]:
        """The braid it makes, round the ring — see
        :func:`~braidpy.take_off.disk_annular_word`."""
        disk = self.disk(n_cycles)
        word, _ = disk_annular_word(
            disk.start, disk.steps, disk.n_slots, clockwise=False
        )
        return word

    def braid(self, n_cycles: int = 1) -> "Braid":
        """The braid it makes, as a flat braid word: the ring's, with the
        middle solid — see :func:`~braidpy.annulus_braid.solid_word`."""
        from braidpy.braid import Braid

        word = solid_word(self.annular_word(n_cycles), self.n_strands)
        return Braid(word or [0], self.n_strands)

    def to_mobidai(self) -> "MobidaiConfig":
        """One cycle as a kumihimo disk (mobidai) pattern — see
        :func:`sinnet_to_mobidai`."""
        return sinnet_to_mobidai(self)

    def animate(self, n_cycles: int = 1, **kwargs):
        """Animate it on its disk, seen from above — see
        :func:`~braidpy.disk_animation.animate_sinnet`."""
        from braidpy.disk_animation import animate_sinnet

        return animate_sinnet(self, n_cycles=n_cycles, **kwargs)

    def braid_3d(self, yarn_diameter: float = 0.12, n_cycles: int = 4, **kwargs):
        """The braid it makes, laid and tightened — see
        :func:`~braidpy.take_off.disk_braid`."""
        disk = self.disk(n_cycles)
        return disk_braid(
            disk.start,
            disk.steps,
            disk.n_slots,
            yarn_diameter,
            clockwise=False,
            **kwargs,
        )


# ============================ On a disk ============================


@dataclass
class SinnetDisk:
    """A sinnet set out on a disk with a slot for every place a strand stops.

    Each space has ``slots_per_space`` slots side by side, its strands kept
    together in the middle of them.  Slots are numbered anticlockwise, as
    the spaces are, from the clockwise end of space 1.

    Attributes:
        n_spaces: Spaces round the disk.
        slots_per_space: Slots in each.
        start: Each strand's slot.  Strands are numbered from 1, space by
            space and anticlockwise within one, as :func:`init_spaces_from_counts`.
        steps: The strand each step moves, and by how many slots: a move,
            over everything it passes, or a few strands sliding along
            together in a space, over nothing.
        labels: What each step is.
    """

    n_spaces: int
    slots_per_space: int
    start: Dict[Hashable, int]
    steps: List[Dict[Hashable, int]]
    labels: List[str]

    @property
    def n_slots(self) -> int:
        return self.n_spaces * self.slots_per_space

    def middle_slot(self, space: int) -> int:
        """The slot in the middle of a space, where its number is written."""
        return (space - 1) * self.slots_per_space + (self.slots_per_space + 1) // 2

    @property
    def slot_offset(self) -> float:
        """How far round the numbering is turned to draw it as the book does:
        space 1 starting on the left, anticlockwise from there."""
        return self.n_slots / 4 + 0.5


def sinnet_disk(sinnet: AshleySolidSinnet, n_cycles: int = 1) -> SinnetDisk:
    """Work a sinnet on a disk, following every strand.

    Each move takes the earliest strand of its space — the right-hand one of
    an odd space, the left-hand one of an even space — round the disk over
    every strand it passes, into its place at the end of the space it goes
    to.  The strands left behind, and those it joins, then slide along
    together to the middle of their spaces, so each space always has room
    either side of its strands.

    Args:
        sinnet: The sinnet.
        n_cycles: How many times its moves are made.

    Returns:
        The disk, and the steps that work it.

    Raises:
        ValueError: If a move is from or to a space that is not there, or
            from a space to itself.
    """
    counts = list(sinnet.initial_counts_per_space)
    n_spaces = len(counts)
    for source, target in sinnet.moves:
        if not (1 <= source <= n_spaces and 1 <= target <= n_spaces):
            raise ValueError(f"Move {source} → {target}: no such space.")
        if source == target:
            raise ValueError(f"Move {source} → {target}: to its own space.")

    # Room for the fullest a space ever gets, and a slot either side.
    fullest = max(counts)
    for _ in range(n_cycles):
        for source, target in sinnet.moves:
            if counts[source - 1]:
                counts[source - 1] -= 1
                counts[target - 1] += 1
                fullest = max(fullest, counts[target - 1])
    width = fullest + 2
    n_slots = n_spaces * width

    groups = init_spaces_from_counts(list(sinnet.initial_counts_per_space))

    def placed(space: int, count: int) -> List[int]:
        first = (space - 1) * width + 1 + (width - count) // 2
        return list(range(first, first + count))

    where: Dict[Hashable, int] = {}
    for space, strands in groups.items():
        where.update(zip(strands, placed(space, len(strands))))
    start: Dict[Hashable, int] = dict(where)
    steps: List[Dict[Hashable, int]] = []
    labels: List[str] = []

    def settle(space: int) -> None:
        """Slide a space's strands to its middle, together."""
        strands = groups[space]
        goal: Dict[Hashable, int] = dict(zip(strands, placed(space, len(strands))))
        shift: Dict[Hashable, int] = {
            k: goal[k] - where[k] for k in strands if goal[k] != where[k]
        }
        if not shift:
            return
        if len(set(shift.values())) != 1:  # never: a space only gains or loses one
            raise AssertionError(f"Space {space} would not slide together.")
        steps.append(shift)
        labels.append(f"settle {space}")
        where.update(goal)

    for _ in range(n_cycles):
        for source, target in sinnet.moves:
            leaving = groups[source]
            if not leaving:
                continue
            odd = source % 2 == 1
            mover = leaving.pop(-1 if odd else 0)
            joining = groups[target]
            if target % 2 == 1:
                there = where[joining[0]] - 1 if joining else placed(target, 1)[0]
                joining.insert(0, mover)
            else:
                there = where[joining[-1]] + 1 if joining else placed(target, 1)[0]
                joining.append(mover)
            gap = (there - where[mover]) % n_slots
            steps.append({mover: gap if odd else gap - n_slots})
            labels.append(f"{source} → {target}")
            where[mover] = there
            settle(source)
            settle(target)
    return SinnetDisk(n_spaces, width, start, steps, labels)


def sinnet_to_mobidai(sinnet: AshleySolidSinnet) -> "MobidaiConfig":
    """One cycle of a sinnet as a kumihimo disk (mobidai) pattern.

    The disk of :func:`sinnet_disk`, numbered as a mobidai is, every move
    made from slot to slot the way the sinnet goes round — anticlockwise
    from an odd space, clockwise from an even one — and every slide made one
    strand at a time, the front one first.  A sinnet whose cycle brings each
    space back to its count brings every slot back too, so the pattern is
    simply repeated.

    Args:
        sinnet: The sinnet.

    Returns:
        The pattern.
    """
    from braidpy.mobidai import MobidaiConfig, Move, Strand

    disk = sinnet_disk(sinnet, 1)
    colours = strand_colours(sinnet.n_strands)
    where = {cast(int, k): slot for k, slot in disk.start.items()}
    strands = [Strand(colours[k - 1], slot) for k, slot in sorted(where.items())]
    moves: List[Move] = []
    for step in disk.steps:
        delta = next(iter(step.values()))
        sense = 1 if delta > 0 else -1
        for k in sorted((cast(int, k) for k in step), key=lambda k: -sense * where[k]):
            target = (where[k] - 1 + delta) % disk.n_slots + 1
            moves.append(Move(where[k], target, sense))
            where[k] = target
    return MobidaiConfig(
        strands=strands,
        moves=moves,
        n_shift_after_cycle=0,
        n_slots=disk.n_slots,
        is_clockwise=False,
    )


def strand_colours(n: int) -> List[str]:
    """A colour per strand, evenly round the hue circle."""
    import matplotlib

    hsv = matplotlib.colormaps["hsv"]
    return [matplotlib.colors.to_hex(hsv(i / max(n, 1))) for i in range(n)]


def init_spaces_from_counts(counts: List[int]) -> Dict[int, List[int]]:
    """Build the mapping sector -> strand IDs from counts.

    Strand IDs are assigned contiguously starting at 1, scanning sectors in ascending order.

    Args:
        counts (List[int]): Number of strands in each sector, length = n_sectors.

    Returns:
        Dict[int, List[int]]: Mapping from sector index (1-based) to list of strand IDs.
    """
    spaces: Dict[int, List[int]] = {}
    strand_id = 1
    for i, c in enumerate(counts, start=1):
        spaces[i] = list(range(strand_id, strand_id + c))
        strand_id += c
    return spaces


def flatten_spaces(spaces: Dict[int, List[int]]) -> List[int]:
    """Flatten the strands from all spaces into a single list in order of space index.

    Args:
        spaces (Dict[int, List[int]]): Space-to-strand mapping.

    Returns:
        List[int]: Flattened list of strand IDs.
    """
    flat = []
    for s in sorted(spaces.keys()):
        flat.extend(spaces[s])
    return flat


def ashley_single_move_to_artin(
    counts: List[int], from_space: int, to_space: int
) -> Tuple[List[int], List[int]]:
    """Apply one Ashley move and return updated counts and the Artin braid word segment.

    The direction is determined by the parity of `from_space`:
      odd -> move right (anticlockwise, increasing sector index), even -> move left (clockwise).
    Wrap-around crosses all other strands in the appropriate Artin order.

    Note:
        This function updates only the per-sector counts. It reconstructs strand IDs
        from counts at each step, so IDs are not persistent across moves. The output
        braid word is computed according to the provided logic but the visualizer
        uses counts only.

    Args:
        counts (List[int]): Current number of strands per sector.
        from_space (int): 1-based starting sector index.
        to_space (int): 1-based destination sector index.

    Returns:
        Tuple[List[int], List[int]]:
            Updated counts after the move, and the list of signed Artin σ generators
            produced during this move.
    """
    n_spaces = len(counts)
    n_strands = sum(counts)
    spaces = init_spaces_from_counts(counts)
    braid_word: List[int] = []

    if spaces[from_space]:
        from_parity = from_space % 2
        moving_right = from_parity == 1  # odd → right

        current_space = from_space
        while current_space != to_space:
            next_space = current_space + (1 if moving_right else -1)

            # Wrap handling
            is_wrapped = False
            if next_space == 0:
                is_wrapped = True
                next_space = n_spaces
                for s in range(n_strands - 1):
                    braid_word.append(-(s + 1))
            elif next_space == n_spaces + 1:
                is_wrapped = True
                next_space = 1
                for s in reversed(range(n_strands - 1)):
                    braid_word.append(s + 1)

            if is_wrapped:
                counts[current_space - 1] -= 1
                counts[next_space - 1] += 1
                spaces = init_spaces_from_counts(counts)

            next_strands = spaces[next_space]
            next_parity = next_space % 2
            insert_shortest = from_parity == next_parity
            if next_space != to_space or not insert_shortest:
                cross_order = (
                    next_strands if moving_right else list(reversed(next_strands))
                )
                for s in cross_order[int(is_wrapped) :]:
                    braid_word.append(-(s - 1) if moving_right else s)

            if not is_wrapped:
                counts[current_space - 1] -= 1
                counts[next_space - 1] += 1
                spaces = init_spaces_from_counts(counts)

            current_space = next_space

    return counts, braid_word


def ashley_to_artin_exact(
    counts: List[int], moves: Dict[int, int] | Sequence[Tuple[int, int]]
) -> Tuple[List[int], List[int]]:
    """Convert an Ashley-style braid (sinnet) into an exact Artin braid word.

    Ashley braids are described in the Ashley book of knots

    The word is read anticlockwise, and counts a strand moved over, seen
    from above, as a positive crossing: the mirror image, read from the
    other side, of :meth:`AshleySolidSinnet.braid`, which reads the braid
    as braidpy draws one.  The two are the same braid.

    This function simulates each strand's movement:
    - Handles wrap-around moves by crossing all other strands in reverse order.
    - Records crossings in correct Artin σ notation.
    - Handles parity-based insertion into the destination space.

    Args:
        counts (List[int]): List of strand counts for each space.
        moves: ``(source, destination)`` spaces, in order.  A mapping from
            source to destination is also read, but cannot hold two moves
            from one space.

    Returns:
        Tuple[List[int], List[int]]:
            - List of Artin σ generators as signed int.
            - Final mapping of spaces to strands.
    """
    braid_word: List[int] = []

    pairs = moves.items() if isinstance(moves, dict) else moves
    for from_space, to_space in pairs:
        counts, braid_seq = ashley_single_move_to_artin(counts, from_space, to_space)
        braid_word.extend(braid_seq)

    return counts, braid_word


# ============================ Visualization ============================


def _sector_bounds(n_spaces: int, idx0: int) -> Tuple[float, float]:
    """Compute angular bounds for a sector.

    Args:
        n_spaces (int): Total number of sectors.
        idx0 (int): 0-based sector index.

    Returns:
        Tuple[float, float]: (theta_start, theta_end) in radians.
    """
    theta1 = 2 * math.pi * idx0 / n_spaces
    theta2 = 2 * math.pi * (idx0 + 1) / n_spaces
    return theta1, theta2


def _path_for_move(n_spaces: int, from_space: int, to_space: int) -> List[int]:
    """Enumerate sector indices visited by a moving strand.

    Movement direction is set by the parity of `from_space`:
      odd -> right, even -> left. Includes wrap-around.

    Args:
        n_spaces (int): Number of sectors.
        from_space (int): 1-based start sector.
        to_space (int): 1-based destination sector.

    Returns:
        List[int]: Sequence of sector indices visited, including start and end.
    """
    if from_space == to_space:
        return [from_space]
    moving_right = (from_space % 2) == 1
    path = [from_space]
    current_space = from_space
    while current_space != to_space:
        next_space = current_space + (1 if moving_right else -1)
        if next_space == 0:
            next_space = n_spaces
        elif next_space == n_spaces + 1:
            next_space = 1
        path.append(next_space)
        current_space = next_space
    return path


def _draw_disk_state(
    axis: Axes,
    counts_per_space: List[int],
    title: str,
    show_ids: bool = True,
    highlight_path: Optional[List[int]] = None,
    r_outer: float = 1.0,
    r_inner: float = 0.5,
    r_strand_circle: float = 0.75,
    arc_pad_frac: float = 0.12,
    strand_colors: Optional[Dict[int, Tuple[float, float, float, float]]] = None,
) -> None:
    """Draw one frame of the disk with colored strands and optional path arrows.

    Args:
        axis (matplotlib.axes.Axes): Axis to draw on.
        counts_per_space (List[int]): Strand counts per sector for this frame.
        title (str): Title for the frame.
        show_ids (bool): If True, render strand IDs inside dots.
        highlight_path (Optional[List[int]]): Sector indices forming an arrow path.
        r_outer (float): Outer radius of the annulus.
        r_inner (float): Inner radius of the annulus.
        r_strand_circle (float): Radius at which strand markers are placed.
        arc_pad_frac (float): Fraction to trim from both ends of each sector arc.
        strand_colors (Optional[Dict[int, Tuple[float, float, float, float]]]):
            Mapping from strand ID to RGBA color. If None, uses black.

    Returns:
        None
    """
    n_spaces = len(counts_per_space)

    # Sectors
    for i in range(n_spaces):
        theta1_deg = 360.0 * i / n_spaces + OFFSET_DEG
        theta2_deg = 360.0 * (i + 1) / n_spaces + OFFSET_DEG
        w = Wedge(
            (0, 0),
            r_outer,
            theta1_deg,
            theta2_deg,
            width=r_outer - r_inner,
            ec="k",
            fc="white",
        )
        axis.add_patch(w)

        theta_mid = math.radians((theta1_deg + theta2_deg) / 2)
        lx = 1.12 * math.cos(theta_mid)
        ly = 1.12 * math.sin(theta_mid)
        axis.text(lx, ly, str(i + 1), ha="center", va="center", fontsize=10)

    # Strands
    spaces = init_spaces_from_counts(counts_per_space)
    for s_idx, strand_ids in spaces.items():
        m = len(strand_ids)
        if not m:
            continue

        theta1, theta2 = _sector_bounds(n_spaces, s_idx - 1)
        arc_length = theta2 - theta1
        pad = arc_length * arc_pad_frac
        a1, a2 = theta1 + pad, theta2 - pad
        thetas = (
            [0.5 * (a1 + a2)]
            if m == 1
            else [a1 + t * (a2 - a1) / (m - 1) for t in range(m)]
        )

        for strand_index, th in zip(strand_ids, thetas):
            x, y = (
                r_strand_circle * math.cos(th + np.deg2rad(OFFSET_DEG)),
                r_strand_circle * math.sin(th + np.deg2rad(OFFSET_DEG)),
            )
            color = (
                strand_colors.get(strand_index, (0, 0, 0, 1))
                if strand_colors
                else (0, 0, 0, 1)
            )
            axis.add_patch(Circle((x, y), 0.02, color=color))
            if show_ids:
                axis.text(
                    x,
                    y,
                    str(strand_index),
                    ha="center",
                    va="center",
                    fontsize=20,
                    color="black",
                )

    # Move path arrows
    if highlight_path and len(highlight_path) >= 2:
        r_arrow = 1.28
        centers = {
            k: (
                r_arrow
                * math.cos(2 * math.pi * (k - 0.5) / n_spaces + np.deg2rad(OFFSET_DEG)),
                r_arrow
                * math.sin(2 * math.pi * (k - 0.5) / n_spaces + np.deg2rad(OFFSET_DEG)),
            )
            for k in range(1, n_spaces + 1)
        }
        for a, b in zip(highlight_path[:-1], highlight_path[1:]):
            xa, ya = centers[a]
            xb, yb = centers[b]
            axis.add_patch(
                FancyArrowPatch(
                    (xa, ya),
                    (xb, yb),
                    arrowstyle="->",
                    mutation_scale=10,
                    lw=2,
                    color="gray",
                )
            )

    axis.set_aspect("equal")
    axis.set_xlim(-1.45, 1.45)
    axis.set_ylim(-1.45, 1.45)
    axis.axis("off")
    axis.set_title(title, fontsize=12)


def visualize_sinnet(
    initial_counts: List[int],
    moves: List[Tuple[int, int]],
    out_dir: str = "ashley_viz",
    prefix: str = "step",
    make_gif: bool = True,
    gif_name: str = "animation.gif",
    show_ids: bool = True,
    r_strand_circle: float = 0.75,
    arc_pad_frac: float = 0.12,
) -> Dict[str, List[str] | str]:
    """Render an Ashley sinnet into step images and an optional GIF.

    See :meth:`AshleySolidSinnet.animate` for an animation that follows
    every strand, and the braid growing beside it.

    This function draws an initial frame, then a frame per move showing the path
    between sectors, then a final frame after all moves. Each strand ID gets a
    consistent color derived from `matplotlib.cm.tab20`.

    Note:
        Colors are assigned by global strand ID computed from `initial_counts`.
        Since IDs are reconstructed from counts at each step, IDs are not
        persistent across moves. If persistent identity is required, use a
        stateful mapping and explicit crossing simulation.

    Args:
        initial_counts (List[int]): Initial counts per sector.
        moves (List[Tuple[int, int]]): List of (from_sector, to_sector) moves, 1-based.
        out_dir (str): Output directory for saved frames and GIF.
        prefix (str): Filename prefix for step images.
        make_gif (bool): If True and imageio is available, save an animated GIF.
        gif_name (str): Filename for the GIF inside `out_dir`.
        show_ids (bool): If True, draw numeric IDs over dots.
        r_strand_circle (float): Radius of the strand circle inside the annulus.
        arc_pad_frac (float): Trim near sector borders to avoid overlaps.

    Returns:
        Dict[str, List[str] | str]: Dictionary containing:
            - "frames": List[str]. Paths to saved PNG frames.
            - "final": str. Path to the final frame.
            - "gif": str. Path to the saved GIF, or a message if skipped.
    """
    os.makedirs(out_dir, exist_ok=True)
    frames: List[str] = []

    # Color map assignment (stable by ID)
    total_strands = sum(initial_counts)
    cmap = cm.get_cmap("tab20", total_strands if total_strands > 0 else 1)
    strand_colors = {
        sid: cmap((sid - 1) % cmap.N) for sid in range(1, total_strands + 1)
    }

    counts = list(initial_counts)

    # Initial
    fig, ax = plt.subplots(figsize=(5, 5))
    _draw_disk_state(
        ax,
        counts,
        "Initial",
        show_ids,
        None,
        r_strand_circle=r_strand_circle,
        arc_pad_frac=arc_pad_frac,
        strand_colors=strand_colors,
    )
    fig.tight_layout()
    p0 = os.path.join(out_dir, f"{prefix}_00.png")
    fig.savefig(p0, dpi=150)
    plt.close(fig)
    frames.append(p0)

    # Steps
    n_spaces = len(counts)
    for i, (frm, to) in enumerate(moves, start=1):
        path = _path_for_move(n_spaces, frm, to)
        fig, ax = plt.subplots(figsize=(5, 5))
        _draw_disk_state(
            ax,
            counts,
            f"Step {i}: {frm} → {to}",
            show_ids,
            highlight_path=path,
            r_strand_circle=r_strand_circle,
            arc_pad_frac=arc_pad_frac,
            strand_colors=strand_colors,
        )
        fig.tight_layout()
        pi = os.path.join(out_dir, f"{prefix}_{i:02d}.png")
        fig.savefig(pi, dpi=150)
        plt.close(fig)
        frames.append(pi)

        counts, _ = ashley_single_move_to_artin(counts, frm, to)

    # Final
    fig, ax = plt.subplots(figsize=(5, 5))
    _draw_disk_state(
        ax,
        counts,
        "Final",
        show_ids,
        None,
        r_strand_circle=r_strand_circle,
        arc_pad_frac=arc_pad_frac,
        strand_colors=strand_colors,
    )
    fig.tight_layout()
    pf = os.path.join(out_dir, "final.png")
    fig.savefig(pf, dpi=150)
    plt.close(fig)
    frames.append(pf)

    result: Dict[str, List[str] | str] = {"frames": frames, "final": pf}

    if make_gif:
        gif_path = os.path.join(out_dir, gif_name)
        imgs: list = [imageio.imread(f) for f in frames]
        imageio.mimsave(gif_path, imgs, loop=0, fps=1)
        result["gif"] = gif_path

    return result


# ============================ Example ============================

if __name__ == "__main__":
    counts0 = [2, 1, 3, 2, 1, 2]
    moves = [(1, 3), (4, 2), (5, 6), (2, 1)]
    output = visualize_sinnet(
        counts0,
        moves,
        out_dir="ashley_demo_arc",
        r_strand_circle=0.75,
        arc_pad_frac=0.10,
    )
    print(output)
