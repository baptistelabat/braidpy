"""
The following braid were taken from "Bracelets Kumihimo, technique des bracelets japonais" by Agnès Delage-Calvet
"""

"""
8 strands on a 32 slots clockwise mobidai

"""

initial_slots = [
    (32, "red"),
    (1, "red"),
    (17, "red"),
    (16, "red"),
    (25, "green"),
    (24, "green"),
    (8, "green"),
    (9, "green"),
]

move = [(1, 15), (17, 31), (25, 7), (9, 23), (16, 30), (32, 14)]

"""
7 strands on a 8 slots clockwise mobidai (0 to 7)
"""
initial_slots = [
    (1, "red"),
    (2, "yellow"),
    (3, "purple"),
    (4, "red"),
    (5, "green"),
    (6, "orange"),
    (7, "blue"),
]

(3, 0)
"""
then rotate(-3) and repeat
"""

"""
12 strands on a 32 slots clockwise mobidai
"""
initial_slots = [
    (1, "yellow"),
    (5, "pink"),
    (6, "pink"),
    (17, "pink"),
    (21, "pink"),
    (22, "pink"),
    (27, "pink"),
    (11, "blue"),
    (12, "red"),
    (16, "purple"),
    (28, "green"),
    (32, "cyan"),
]

move = [(1, 15), (17, 31), (28, 10), (12, 26), (22, 4), (6, 20)]

"""
16 strands on a 32 slots clockwise mobidai
"""
initial_slots = [
    (32, "green"),
    (1, "red"),
    (17, "green"),
    (16, "green"),
    (25, "red"),
    (24, "green"),
    (8, "red"),
    (9, "red"),
    (4, "red"),
    (5, "red"),
    (12, "red"),
    (13, "red"),
    (20, "green"),
    (21, "green"),
    (28, "red"),
    (29, "red"),
]

move = [(1, 15), (17, 31), (29, 11), (13, 27), (25, 7), (9, 23), (21, 3), (5, 19)]
