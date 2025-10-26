from typing import Dict, List, Tuple


def init_spaces_from_counts(counts: List[int]) -> Dict[int, List[int]]:
    """Initialize the mapping of spaces to their strand IDs.

    Args:
        counts (List[int]): Number of strands in each space.

    Returns:
        Dict[int, List[int]]: Mapping from space index (1-based) to list of strand IDs.
    """
    spaces = {}
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


def ashley_to_artin_exact(
    counts: List[int], moves: Dict[int, int]
) -> Tuple[List[str], Dict[int, List[int]]]:
    """Convert an Ashley-style braid (sinnet) into an exact Artin braid word.

    Ashley braids are described in the Ashley book of knots

    This function simulates each strand's movement:
    - Handles wrap-around moves by crossing all other strands in reverse order.
    - Records crossings in correct Artin σ notation.
    - Handles parity-based insertion into the destination space.

    Args:
        counts (List[int]): List of strand counts for each space.
        moves (Dict[int, int]): Mapping from source space to destination space.

    Returns:
        Tuple[List[str], Dict[int, List[int]]]:
            - List of Artin σ generators as strings.
            - Final mapping of spaces to strands.
    """
    spaces = init_spaces_from_counts(counts)
    m = len(spaces)
    braid_word: List[str] = []

    for from_space, to_space in moves.items():
        if not spaces[from_space]:
            continue

        # Determine moving strand and direction
        from_parity = from_space % 2
        to_parity = to_space % 2
        moving_right = from_parity == 1  # odd → right

        # Pop strand from source space
        strand = spaces[from_space].pop(-1 if moving_right else 0)

        # Flatten spaces for global indexing
        flat = flatten_spaces(spaces)

        # Determine if this move wraps around
        if moving_right and to_space < from_space:
            wrap_around = True
        elif not moving_right and to_space > from_space:
            wrap_around = True
        else:
            wrap_around = False

        # --- Cross strands in intermediate spaces ---
        if wrap_around:
            # Crossing all other strands in reverse order
            for s in reversed(flat):
                idx = flat.index(s)
                braid_word.append(f"σ{idx + 1}" + ("" if moving_right else "⁻¹"))
                flat[idx], strand = strand, flat[idx]
        else:
            # Normal step-by-step movement through spaces
            current_space = from_space
            while current_space != to_space:
                next_space = current_space + (1 if moving_right else -1)
                if next_space < 1:
                    next_space = m
                elif next_space > m:
                    next_space = 1

                next_strands = spaces[next_space]
                cross_order = (
                    next_strands if moving_right else list(reversed(next_strands))
                )
                for s in cross_order:
                    idx = flat.index(s)
                    braid_word.append(f"σ{idx + 1}" + ("" if moving_right else "⁻¹"))
                    flat[idx], strand = strand, flat[idx]

                current_space = next_space

        # --- Cross strands already in destination space ---
        same_parity = from_parity == to_parity
        insert_right = moving_right if same_parity else not moving_right
        dest_strands = spaces[to_space]
        cross_order = dest_strands if insert_right else list(reversed(dest_strands))
        for s in cross_order:
            idx = flat.index(s)
            braid_word.append(f"σ{idx + 1}" + ("" if insert_right else "⁻¹"))
            flat[idx], strand = strand, flat[idx]

        # --- Insert strand in destination space ---
        if insert_right:
            spaces[to_space].append(strand)
        else:
            spaces[to_space].insert(0, strand)

    return braid_word, spaces


# Example usage
if __name__ == "__main__":
    counts_3042 = [2, 1, 1, 2, 1, 1]
    moves_3042 = {1: 5, 2: 4, 3: 1, 4: 2, 5: 3, 6: 4}

    word, final_spaces = ashley_to_artin_exact(counts_3042, moves_3042)
    print("Exact Artin braid word:")
    print(" ".join(word))
    print("\nFinal space layout:")
    for s in sorted(final_spaces.keys()):
        print(f"Space {s}: {final_spaces[s]}")
