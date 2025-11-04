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
