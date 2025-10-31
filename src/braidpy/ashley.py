from typing import Dict, List, Tuple


def init_spaces_from_counts(counts: List[int]) -> Dict[int, List[int]]:
    """Based on the initial nnumber of strands in each space of the disk described by Ashley,
    initialize the mapping of spaces to their strand IDs.

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


def ashley_single_move_to_artin(counts: list[int], from_space: int, to_space: int):
    """Simulate one step

    Args:
        counts (list[int]): number of strands in each zone
        from_space (int): starting space
        to_space (int): space to go

    Returns:
        Tuple[list[int], list[int]]:
            - list of counts of number of strand in each zone
            - list of Artin σ generators as signed int.
    """
    n_spaces = len(counts)
    n_strands = sum(counts)
    spaces = init_spaces_from_counts(counts)
    braid_word: list[int] = []
    if spaces[from_space]:
        # Determine moving strand and direction
        from_parity = from_space % 2

        moving_right = from_parity == 1  # odd → right

        # Normal step-by-step movement through spaces
        current_space = from_space
        while current_space != to_space:
            next_space = current_space + (1 if moving_right else -1)

            # Deals with wrapping to go from annulus to flat braid numbering
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
                counts[next_space - 1] += 1  # 1 based -> zero based
                spaces = init_spaces_from_counts(counts)

            next_strands = spaces[next_space]
            next_parity = next_space % 2
            insert_shortest = from_parity == next_parity
            if next_space != to_space or not (insert_shortest):
                cross_order = (
                    next_strands if moving_right else list(reversed(next_strands))
                )
                for s in cross_order[int(is_wrapped) :]:
                    braid_word.append(-(s - 1) if moving_right else s)

            if not (is_wrapped):
                counts[current_space - 1] -= 1
                counts[next_space - 1] += 1  # 1 based -> zero based
                spaces = init_spaces_from_counts(counts)
            current_space = next_space

    return (
        counts,
        braid_word,
    )


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
        Tuple[List[int], List[int]]:
            - List of Artin σ generators as signed int.
            - Final mapping of spaces to strands.
    """
    braid_word: List[int] = []

    for from_space, to_space in moves.items():
        counts, braid_seq = ashley_single_move_to_artin(counts, from_space, to_space)
        braid_word.extend(braid_seq)

    return counts, braid_word
