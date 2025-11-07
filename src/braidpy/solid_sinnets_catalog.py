from ashley_solid_sinnet import AshleySolidSinnet

"""
ABOK #3042
8-strand round
"""
abok_3042 = AshleySolidSinnet(
    initial_counts_per_space=[2, 1, 1, 2, 1, 1],
    moves=[(1, 5), (4, 2), (5, 3), (2, 6), (3, 1), (6, 4)],
)

"""
ABOK #3043
11-strand triangle
"""
abok_3043 = AshleySolidSinnet(
    initial_counts_per_space=[3, 1, 2, 2, 2, 1],
    moves=[(1, 5), (4, 2), (5, 3), (2, 6), (3, 1), (6, 4)],
)

"""
ABOK #3044
8-strand triangle
"""
abok_3044 = AshleySolidSinnet(
    initial_counts_per_space=[2, 1, 1, 1, 1, 2],
    moves=[(1, 5), (6, 4), (5, 3), (4, 2), (3, 1), (2, 6)],
)

"""
ABOK #3045
10-strand triangle
"""
abok_3045 = AshleySolidSinnet(
    initial_counts_per_space=[2, 1, 2, 2, 1, 2],
    moves=[(1, 5), (4, 2), (3, 1), (6, 4), (5, 3), (2, 6)],
)

"""
ABOK #3046
13-strand triangle
"""
abok_3046 = AshleySolidSinnet(
    initial_counts_per_space=[3, 2, 3, 2, 2, 1],
    moves=[(1, 5), (2, 6), (3, 1), (4, 2), (5, 3), (6, 4)],
)

"""
ABOK #3047
19-strand triangle
"""
abok_3047 = AshleySolidSinnet(
    initial_counts_per_space=[2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1, 2],
    moves=[
        (1, 9),
        (8, 2),
        (3, 7),
        (6, 4),
        (5, 1),
        (12, 6),
        (7, 11),
        (10, 8),
        (9, 5),
        (4, 10),
        (11, 3),
        (2, 12),
    ],
)

"""
ABOK #3048
17-strand triangle
"""
abok_3048 = AshleySolidSinnet(
    initial_counts_per_space=[2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 1],
    moves=[
        (1, 9),
        (8, 2),
        (3, 7),
        (6, 4),
        (9, 1),
        (4, 10),
        (11, 3),
        (2, 12),
        (5, 1),
        (12, 6),
        (7, 11),
        (10, 8),
    ],
)
