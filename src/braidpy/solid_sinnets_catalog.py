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
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3045 = AshleySolidSinnet(
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
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
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

"""
ABOK #3049
22-strand triangle
https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""
abok_3049 = AshleySolidSinnet(
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
    initial_counts_per_space=[2, 1, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
    moves=[
        (11, 13),
        (12, 2),
        (3, 11),
        (10, 4),
        (5, 9),
        (8, 6),
        (7, 1),
        (18, 8),
        (9, 17),
        (1, 10),
        (11, 15),
        (14, 12),
        (13, 7),
        (6, 14),
        (15, 5),
        (4, 16),
        (17, 3)(2, 18),
    ],
)
"""
ABOK #3052
20-strand hexagon
"""
abok_3052 = AshleySolidSinnet(
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
https://www.facebook.com/johnrichings/posts/pfbid0pJh7t4KgQWMeJWx4SQHg18dqaT2G1Ho1YmmNqFJto2MraFz4muHhFSgWuZSr33ual?__cft__[0]=AZVUW5RGsiw4yNeTJFgAEDXQa2P_45OG9mKgp7qtJERvN-9bgI_t09zqey1iIH1R4T_CwcqAidQGqFwEWonDNvPP1_Z0O-g-N2ZKAtXa0QPLzPoIbWXmpO99HXBlCQJAPxDE05WW9o0gPtt5JD7FD9Op9EzZWqPC0nlLDBjxc2x23A&__tn__=%2CO%2CPH-R
"""
abok_3054 = AshleySolidSinnet(
    initial_counts_per_space=[3, 1, 2, 1, 2, 2, 2, 1, 2, 1], moves=abok_3053.moves
)

"""
ABOK #3056 https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""

"""
ABOK #3074 https://www.facebook.com/johnrichings/posts/pfbid0sFpnjdzXANcj4NSp2ZK5B3C2vNpLnnWZ9X7ytgxx4e6aqxPwLto4NLsca6waPty4l
"""


"""
16 Strand Pentagon
ABOK #3080
https://www.facebook.com/photo/?fbid=499834040106245&set=a.134484456641207
"""

"""
ABOK #3081 https://www.youtube.com/watch?v=FDMqYdqFHtU
"""

"""
61-strand
ABOK #3082
https://www.youtube.com/watch?v=_Ydpx9smLAk
https://www.youtube.com/watch?v=w1PJb4Bxb2c
"""

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
