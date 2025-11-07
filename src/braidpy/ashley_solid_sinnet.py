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
from typing import Dict, List, Tuple, Optional
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge, FancyArrowPatch, Circle
import matplotlib.cm as cm
from matplotlib.axes import Axes

import imageio.v2 as imageio  # optional for GIF

OFFSET_DEG = 180  # To match Ahsley book of knots
# ============================ Core Structures ============================


@dataclass
class AshleySolidSinnet:
    """Ashley-style braid pattern.

    Attributes:
        initial_counts_per_space (List[int]): Number of strands per sector. 1-based sectors.
        moves (List[Tuple[int, int]]): Sequence of (from_sector, to_sector) moves, each 1-based.
    """

    initial_counts_per_space: List[int]
    moves: List[Tuple[int, int]]


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
        imgs = [imageio.imread(f) for f in frames]
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
