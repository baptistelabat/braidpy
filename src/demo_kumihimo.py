from braidpy import Braid
from braidpy.braid_catalog import square4
from braidpy.braidword import braidword_alpha_to_numeric
from braidpy.handles_reduction import dehornoy_reduce_core

# We started from a kuhimino like braid
# We have 4 strands
# Number 1 is at the top (This would correspond to 32 on a Mobidai
# Number 2 on the left (This would correspond to 24 on a Mobidai)
# Number 3 at the bottom (This would correspond to 16 on a Mobidai)
# Number 4 on the right (This would correspond to 8 on a mobidai)
# (We count from 1 to 4 anticlockwise)

# We do the following steps:
# 1<->3 crossing to the right
# 2<->4 crossing to the right
# 1<->3 crossing to the left
# 2<->4 crossing to the left
# and so on

# We are close to https://www.youtube.com/watch?v=zYJpuaHT06E but note that usually on the kuhimino 1<->3 is always left and 2<->4 always right for the 4 strands
# kuhimino


top_bottom_right = "Aba"
left_right_right = "Bcb"
top_bottom_left = "ABa"
left_right_left = "BCb"

b_top_bottom_right = Braid(braidword_alpha_to_numeric(top_bottom_right), n_strands=4)
b_left_right_right = Braid(braidword_alpha_to_numeric(left_right_right), n_strands=4)
b_top_bottom_left = Braid(braidword_alpha_to_numeric(top_bottom_left), n_strands=4)
b_left_right_left = Braid(braidword_alpha_to_numeric(left_right_left), n_strands=4)

b = b_top_bottom_right * b_left_right_right * b_top_bottom_left * b_left_right_left

b.draw()
b_reduced = Braid(dehornoy_reduce_core(b.generators).generators, n_strands=4)
print(" ")
b_reduced.draw()
print(" ")

b4, n = square4()
b4_reduced = Braid(dehornoy_reduce_core((b4**4).generators).generators, n_strands=4)
print(" ")
print(b4_reduced.generators)
b4_reduced.draw()
