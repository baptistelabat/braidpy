# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Ashley's solid sinnets, from *The Ashley Book of Knots*: each its own
:class:`~braidpy.ashley_solid_sinnet.AshleySolidSinnet`, named by its number
in the book, and all of them in :data:`CATALOGUE`, as every catalogue lists
its braids (:mod:`braidpy.catalogue`)."""

from braidpy.ashley_solid_sinnet import AshleySolidSinnet
from braidpy.catalogue import Entry

"""The simplest sinnets, worked the same way on the stand: Ashley's stand,
like a marudai, makes the plait and the square and round sinnets as well
as the solid sinnets it is in the book for, and seeing them made there
helps to understand the bigger ones."""

# Laid out as the book is, rows of counts and all: not reflowed.
# fmt: off
"""
ABOK #2965
3-strand flat
The plait.
"""
abok_2965 = AshleySolidSinnet(
    shape="flat",
    initial_counts_per_space=[2, 1],
    moves=[(1, 2), (2, 1)],
)

"""
ABOK #2999
4-strand square
"""
abok_2999 = AshleySolidSinnet(
    shape="square",
    initial_counts_per_space=[1, 1, 1, 1],
    moves=[(1, 3), (3, 1), (2, 4), (4, 2)],
)

"""
ABOK #3021
6-strand round
"""
abok_3021 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[1, 1, 1, 1, 1, 1],
    moves=[(1, 3), (3, 5), (5, 1), (2, 6), (6, 4), (4, 2)],
)

"""
ABOK #3042
8-strand round
"""
abok_3042 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 1, 1, 2, 1, 1],
    moves=[(1, 5), (4, 2), (5, 3), (2, 6), (3, 1), (6, 4)],
)

"""
ABOK #3043
11-strand triangle
"""
abok_3043 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[3, 1, 2, 2, 2, 1],
    moves=[(1, 5), (4, 2), (5, 3), (2, 6), (3, 1), (6, 4)],
)

"""
ABOK #3044
8-strand triangle
"""
abok_3044 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 1, 1, 1, 1, 2],
    moves=[(1, 5), (6, 4), (5, 3), (4, 2), (3, 1), (2, 6)],
)

"""
ABOK #3045
10-strand triangle
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3045 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 1, 2, 2, 1, 2],
    moves=[(1, 5), (4, 2), (3, 1), (6, 4), (5, 3), (2, 6)],
)

"""
ABOK #3046
13-strand triangle
"Any sinnet with Il1l uneven
mnnber of edges (or sides), in
order to be symmetrical, must
have all the strands at the edges
rotate in the same direction."
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3046 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[3, 2, 3, 2, 2, 1],
    moves=[(1, 5), (2, 6), (3, 1), (4, 2), (5, 3), (6, 4)],
)

"""
ABOK #3047
19-strand triangle
"""
abok_3047 = AshleySolidSinnet(
    shape="triangle",
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
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3048 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 1],
    moves=[
        (1, 9),
        (8, 2),
        (3, 7),
        (6, 4),
        # (9, 1) as transcribed, which gives space 1 two strands a cycle and
        # space 5 none: #3047's moves on the same twelve spaces are these
        # very moves with (9, 5), the cycle 1 > 9 > 5 > 1.
        (9, 5),
        (4, 10),
        (11, 3),
        (2, 12),
        (5, 1),
        (12, 6),
        (7, 11),
        (10, 8),
    ],
)

"""
ABOK #3049
22-strand triangle
https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""
abok_3049 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[3, 1, 2, 1, 3, 2, 1, 2, 2, 2, 1, 2],
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
ABOK #3050
29-strand triangle
"""
abok_3050 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[3, 2, 3, 2, 2, 3, 2, 3, 2, 2, 3, 2],
    moves=abok_3048.moves,
)
"""
ABOK #3051
28-strand triangle

https://www.youtube.com/watch?v=u1Pc5vE0Rfw
https://www.youtube.com/watch?v=2eV8z6674xM
https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""
abok_3051 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 1, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
    moves=[
        # (11, 13) in the book: 1 gave nothing, 11 twice.
        (1, 13),
        (12, 2),
        (3, 11),
        (10, 4),
        (5, 9),
        (8, 6),
        (7, 1),
        (18, 8),
        (9, 17),
        (16, 10),  # (1, 10) in the book: 16 gave nothing, 1 twice.
        (11, 15),
        (14, 12),
        (13, 7),
        (6, 14),
        (15, 5),
        (4, 16),
        (17, 3),
        (2, 18),
    ],
)
"""
ABOK #3052
20-strand hexagon
"""
abok_3052 = AshleySolidSinnet(
    shape="hexagon",
    initial_counts_per_space=[2, 1, 2, 1, 2, 2, 2, 1, 2, 1, 2, 2],
    moves=[
        (12, 8),
        (7, 1),  # Unsure of these lines
        (1, 7),
        (6, 2),
        (2, 10),
        (9, 3),
        (3, 9),
        (8, 4),
        (4, 12),
        (11, 5),
        (5, 11),
        (10, 6),
    ],
)

"""In these diagrams, for the first time a strand from an
odd-numbered space is led to an even-numbered space, and a strand
from an even-numbered space is led to an odd-numbered space."""
"""
ABOK #3053
19-strand half hexagon
"""
abok_3053 = AshleySolidSinnet(
    shape="half hexagon",
    initial_counts_per_space=[3, 1, 2, 1, 2, 2, 3, 1, 3, 1],
    moves=[
        (6, 4),
        (3, 7),  # Unsure of these lines
        (7, 2),
        (1, 8),
        (8, 5),
        (4, 9),
        (9, 3),
        (2, 10),
        (10, 6),
        (5, 1),
    ],
)

"""
ABOK #3054
17-strand half round
The same moves as #3053.
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3054 = AshleySolidSinnet(
    shape="half round",
    initial_counts_per_space=[3, 1, 2, 1, 2, 2, 2, 1, 2, 1],
    moves=[
        (6, 4),
        (3, 7),
        (7, 2),
        (1, 8),
        (8, 5),
        (4, 9),
        (9, 3),
        (2, 10),
        (10, 6),
        (5, 1),
    ],
)

"""
ABOK #3055
26-strand fanbelt
"""
abok_3055 = AshleySolidSinnet(
    shape="fanbelt",
    initial_counts_per_space=[
        2, 2, 1, 2, 1, 2, 1, 2,
        1, 2, 2, 2, 2, 1, 2, 1,
    ],
    moves=[
        (12, 7),
        (6, 13),
        (13, 5),
        (4, 14),
        (15, 3),
        (2, 16),
        (1, 12),
        (11, 2),
        (3, 11),
        (10, 4),
        (5, 9),
        (8, 6),
        (7, 1),
        (16, 8),
        (9, 15),
        (14, 10),
    ],
)

"""
ABOK #3056
26-strand diamond
ABOK #3056 https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""
abok_3056 = AshleySolidSinnet(
    shape="diamond",
    initial_counts_per_space=[
        2, 1, 2, 1, 2, 2, 1, 2,
        2, 1, 2, 1, 2, 2, 1, 2,
    ],
    moves=[
        (1, 12),
        (11, 2),
        (3, 10),
        (9, 4),
        (6, 1),
        (16, 7),
        (8, 15),
        (14, 9),
        (2, 16),
        (15, 3),
        (4, 14),
        (13, 5),
        (5, 13),
        (12, 6),
        (7, 11),
        (10, 8),
    ],
)

"""
ABOK #3057
9-strand triangle
"""
abok_3057 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 2, 2, 1, 1, 1],
    moves=[
        (1, 5),
        (2, 4),
        (3, 1),
        (4, 6),
        (5, 3),
        (6, 2),
    ],
)

"""
ABOK #3058
9-strand triangle
All strands move to the right.
"""
abok_3058 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 2, 2, 1, 1, 1],
    moves=[
        (1, 5),
        (2, 4),
        (3, 1),
        (4, 6),
        (5, 3),
        (6, 2),
    ],
)

"""
ABOK #3059
13-strand triangle
All strands move to the right.
"""
abok_3059 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 2, 2, 2, 1, 1, 1, 1, 1],
    moves=[
        (1, 7),
        (2, 6),
        (3, 5),
        (4, 1),
        (5, 9),
        (6, 8),
        (7, 4),
        (8, 3),
        (9, 2),
    ],
)

"""
ABOK #3060
9-strand triangle
Strands move right and left.
"""
abok_3060 = AshleySolidSinnet(
    shape="triangle",
    initial_counts_per_space=[2, 1, 1, 1, 2, 2],
    moves=[
        (1, 3),
        (6, 4),
        (5, 1),
        (4, 2),
        (3, 5),
        (2, 6),
    ],
)

"""
ABOK #3061
12-strand square
With a core.
"""
abok_3061 = AshleySolidSinnet(
    shape="square",
    initial_counts_per_space=[2, 2, 1, 1, 2, 1, 2, 1],
    moves=[
        (2, 8),
        (1, 3),
        (8, 6),
        (7, 1),
        (6, 4),
        (5, 7),
        (4, 2),
        (3, 5),
    ],
)

"""
ABOK #3062
26-strand round
"""
abok_3062 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 3],
    moves=[
        (12, 8),
        (7, 1),
        (1, 7),
        (6, 2),
        (2, 10),
        (9, 3),
        (3, 9),
        (8, 4),
        (4, 12),
        (11, 5),
        (5, 11),
        (10, 6),
    ],
)

"""
ABOK #3063
45-strand round
"""
abok_3063 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[
        3, 2, 3, 3, 2, 3, 2, 3, 2,
        2, 3, 2, 2, 3, 2, 3, 2, 3,
    ],
    moves=[
        (16, 12),
        (11, 17),
        (18, 10),
        (1, 9),
        (8, 2),
        (3, 7),
        (4, 18),
        (17, 5),
        (6, 16),
        (7, 15),
        (14, 8),
        (9, 13),
        (10, 6),
        (5, 11),
        (12, 4),
        (13, 3),
        (2, 14),
        (15, 1),
    ],
)

"""
ABOK #3064
19-strand round
"""
abok_3064 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[
        1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1,
    ],
    moves=[
        (7, 11),
        (6, 12),
        (5, 1),
        (4, 2),
        (11, 3),
        (10, 4),
        (9, 5),
        (8, 6),
        (3, 7),
        (2, 8),
        (1, 9),
        (12, 10),
    ],
)

"""
ABOK #3065
9-strand round
"""
abok_3065 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 1, 2, 1, 2, 1],
    moves=[
        (5, 2),
        (1, 4),
        (3, 6),
        (2, 5),
        (4, 1),
        (6, 3),
    ],
)

"""
ABOK #3066
10-strand round
All strands move to the right.
"""
abok_3066 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 1, 1, 1, 2, 1, 1, 1],
    moves=[
        (1, 2),
        (5, 6),
        (2, 3),
        (6, 7),
        (3, 4),
        (7, 8),
        (4, 5),
        (8, 1),
    ],
)
"""
ABOK #3068
12-strand round
All strands move to the right.
"""
abok_3068 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 2, 2, 2, 2, 2],
    moves=[
        (1, 4),
        (4, 1),
        (2, 5),
        (5, 2),
        (3, 6),
        (6, 3),
    ],
)

"""
ABOK #3069
6-strand round
All strands move to the right.
"""
abok_3069 = AshleySolidSinnet(
    shape="round",
    initial_counts_per_space=[2, 2, 1, 1],
    moves=[
        (1, 3),
        (2, 4),
        (3, 1),
        (4, 2),
    ],
)

"""
ABOK #3070
8-strand square
Odd strands move right; even strands move left.
"""
abok_3070 = AshleySolidSinnet(
    shape="square",
    initial_counts_per_space=[2, 2, 2, 2],
    moves=[
        (1, 3),
        (3, 1),
        (2, 4),
        (4, 2),
    ],
)

"""
ABOK #3071
14-strand chisel-edge
Odd strands move right; even strands move left.
"""
abok_3071 = AshleySolidSinnet(
    shape="chisel-edge",
    initial_counts_per_space=[2, 1, 2, 1, 3, 2, 1, 2],
    moves=[
        (5, 1),
        (8, 2),
        (3, 7),
        (6, 4),
        (1, 5),
        (4, 6),
        (7, 3),
        (2, 8),
    ],
)

"""
ABOK #3072
20-strand chisel-edge
Odd strands move right; even strands move left.
"""
abok_3072 = AshleySolidSinnet(
    shape="chisel-edge",
    initial_counts_per_space=[
        2, 1, 2, 1, 2, 1, 3, 2, 1, 2, 1, 2,
    ],
    moves=[
        (7, 1),
        (12, 2),
        (3, 11),
        (10, 4),
        (5, 9),
        (8, 6),
        (1, 7),
        (6, 8),
        (9, 5),
        (4, 10),
        (11, 3),
        (2, 12),
    ],
)

"""
ABOK #3073
20-strand square
"""
abok_3073 = AshleySolidSinnet(
    shape="square",
    initial_counts_per_space=[2, 2, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1],
    moves=[
        (2, 12),
        (11, 3),
        (4, 10),    # explicitly marked Left in the table
        (10, 4),    # explicitly marked Left in the table
        (5, 9),
        (8, 6),
        (3, 5),
        (6, 2),
        (1, 7),
        (7, 1),
        (12, 8),
        (9, 11),
    ],
)

"""
ABOK #3074
26-strand square
https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""

abok_3074 = AshleySolidSinnet(
    shape="square",
    initial_counts_per_space=[
        2, 2, 1, 2, 2, 1, 2, 1,
        2, 2, 1, 2, 2, 1, 2, 1,
    ],
    moves=[
        (2, 16),
        (15, 3),
        (4, 14),
        (13, 5),
        (5, 13),
        (12, 6),
        (7, 11),
        (10, 8),
        (6, 4),
        (3, 7),
        (8, 2),
        (1, 9),
        (9, 1),
        (16, 10),
        (11, 15),
        (14, 12),
    ],
)

"""
ABOK #3075
20-strand oblong
"""
abok_3075 = AshleySolidSinnet(
    shape="oblong",
    initial_counts_per_space=[
        2, 2, 1, 2, 1, 2, 2, 2, 1, 2, 1, 2,
    ],
    moves=[
        (2, 12),
        (12, 3),
        (4, 11),
        (10, 5),
        (6, 9),
        (8, 6),
        (5, 7),
        (7, 4),
        (3, 8),
        (9, 2),
        (1, 10),
        (11, 1),
    ],
)

"""
ABOK #3076
20-strand oblong
"""
abok_3076 = AshleySolidSinnet(
    shape="oblong",
    initial_counts_per_space=[
        2, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1, 2,
    ],
    moves=[
        (4, 2),
        (1, 5),
        (6, 1),
        (12, 7),
        (7, 11),
        (10, 8),
        (2, 12),
        (11, 3),
        (3, 10),
        (9, 4),
        (5, 9),
        (8, 6),
    ],
)

"""
ABOK #3077
32-strand oblong
"""
abok_3077 = AshleySolidSinnet(
    shape="oblong",
    initial_counts_per_space=[
        2, 2, 1, 2, 1, 2, 1, 2, 2, 1,
        2, 2, 1, 2, 1, 2, 1, 2, 2, 1,
    ],
    moves=[
        (2, 20),
        (19, 3),
        (4, 19),
        (18, 5),
        (6, 17),
        (16, 7),
        (8, 15),
        (14, 9),
        (9, 13),
        (12, 10),
        (10, 8),
        (7, 11),
        (11, 6),
        (5, 12),
        (13, 4),
        (3, 14),
        (15, 2),
        (1, 16),
        (17, 1),
        (20, 18),
    ],
)

"""
ABOK #3078
20-strand ellipse
"""
abok_3078 = AshleySolidSinnet(
    shape="ellipse",
    initial_counts_per_space=[
        2, 1, 1, 2, 1, 1, 2, 1, 1, 2,
        1, 2, 2, 1,
    ],
    moves=[
        (1, 3),
        (4, 14),
        (13, 5),
        (12, 6),  # (11, 6) as transcribed: 12 gave nothing, 11 twice.
        (7, 11),
        (10, 8),
        (8, 13),
        (14, 7),
        (6, 1),
        (5, 9),
        (9, 4),
        (3, 10),
        (11, 2),
        (2, 12),
    ],
)

"""
ABOK #3079
36-strand pentagon
"""
abok_3079 = AshleySolidSinnet(
    shape="pentagon",
    # Transcribed with two more spaces, 21 and 22, holding 1 and 2: no move
    # uses them, and without them the strands are the 36 of the note.
    initial_counts_per_space=[
        3, 1, 2, 1, 3, 1, 2, 1, 3, 2,
        1, 2, 1, 2, 2, 2, 1, 2, 2, 2,
    ],
    moves=[
        (1, 13),
        (12, 2),
        (3, 11),
        (10, 4),
        (5, 17),
        (16, 6),
        (7, 15),
        (14, 8),
        (9, 1),
        (20, 10),
        (11, 19),
        (18, 12),
        (13, 5),
        (4, 14),
        (15, 3),
        (2, 16),
        (17, 9),
        (8, 18),
        (19, 7),
        (6, 20),
    ],
)

"""
ABOK #3080
16-strand pentagon
https://www.facebook.com/photo/?fbid=499834040106245&set=a.134484456641207

"""
abok_3080 = AshleySolidSinnet(
    shape="pentagon",
    initial_counts_per_space=[
        2, 1, 2, 1, 2, 2, 1, 2, 1, 2,
    ],
    moves=[
        (1, 7),
        (6, 2),
        (3, 9),
        (8, 4),
        (5, 1),
        (10, 6),
        (7, 3),
        (2, 8),
        (9, 5),
        (4, 10),
    ],
)

"""
ABOK #3081
31-strand pentalpha
https://www.youtube.com/watch?v=FDMqYdqFHtU
"""
abok_3081 = AshleySolidSinnet(
    shape="pentalpha",
    initial_counts_per_space=[
        3, 1, 1, 1, 3,
        1, 1, 1, 3, 1,
        1, 2, 2, 1, 2,
        1, 2, 2, 1, 1,
    ],
    moves=[
        (18, 16),
        (15, 19),
        (1, 13),
        (12, 2),
        # (2, 10) and (15, 9), as first transcribed for the book's (2, 20)
        # and (15, 19), gave spaces 9 and 10 two strands a cycle and 19 and
        # 20 none.  The even spaces are one cycle,
        # 18 > 16 > 6 > 4 > 14 > 12 > 2 > 20 > 10 > 8 > 18, and the odd
        # ones two, 1 > 13 > 5 > 17 > 9 > 1 and 19 > 3 > 7 > 11 > 15 > 19.
        (2, 20),
        (19, 3),
        (5, 17),
        (16, 6),
        (6, 4),
        (3, 7),
        (9, 1),
        (20, 10),
        (10, 8),
        (7, 11),
        (13, 5),
        (4, 14),
        (14, 12),
        (11, 15),
        (17, 9),
        (8, 18),
    ],
)

"""
ABOK #3082
61-strand pentalpha
https://www.youtube.com/watch?v=_Ydpx9smLAk
https://www.youtube.com/watch?v=w1PJb4Bxb2c
"""
abok_3082 = AshleySolidSinnet(
    shape="pentalpha",
    initial_counts_per_space=[
        3, 1, 2, 1, 1, 1, 2, 1, 3, 1,
        2, 1, 1, 1, 2, 1, 3, 1, 2, 1,
        1, 2, 1, 2, 2, 1, 2, 1, 2, 1,
        2, 1, 2, 2, 1, 2, 1, 1, 2, 1,
    ],
    moves=[
        (34, 32),
        (31, 35),
        (36, 30),
        (29, 37),
        (1, 25),
        (24, 2),
        (3, 23),
        (22, 4),
        (2, 40),
        (39, 3),
        (4, 38),
        (37, 5),
        (9, 33),
        (32, 10),
        (11, 31),
        (30, 12),
        (10, 8),
        (7, 11),
        (12, 6),
        (5, 13),
        (17, 1),
        (40, 18),
        (19, 39),
        (38, 20),
        (18, 16),
        (15, 19),
        (20, 14),
        (13, 21),
        (25, 9),
        (8, 26),
        (27, 7),
        (6, 28),
        (26, 24),
        (23, 27),
        (28, 22),
        (21, 29),
        (33, 17),
        (16, 34),
        (35, 15),
        (14, 36),
    ],
)



"""
82-strand pentagonal sinnet
3082-2 By Norbert Trupiano
http://charles.hamel.free.fr/knots-and-cordages/PUBLICATIONS/Solid%20Sinnet%20variations.pdf
"""

"""
97-strand eight points
3082-3 By Norbert Trupiano
http://charles.hamel.free.fr/knots-and-cordages/PUBLICATIONS/Solid%20Sinnet%20variations.pdf
"""


"""
121-strand Pentalpha
https://www.youtube.com/watch?v=BPxj2Z9UYR0&t=664s
"""

"""
127-strand 7-branch star
By John Richings
https://www.facebook.com/photo?fbid=598774186878896&set=pcb.598774553545526
"""


# fmt: on


def _entry(name: str, sinnet: AshleySolidSinnet) -> Entry[AshleySolidSinnet]:
    number = name.split("_")[1]
    return Entry(
        title=f"ABOK #{number}, {sinnet.n_strands}-strand {sinnet.shape or 'sinnet'}",
        make=lambda: sinnet,
        reference=f"The Ashley Book of Knots, #{number}",
    )


# By their number in the book.
CATALOGUE: dict[str, Entry[AshleySolidSinnet]] = {
    name: _entry(name, value)
    for name, value in sorted(globals().items())
    if isinstance(value, AshleySolidSinnet)
}
