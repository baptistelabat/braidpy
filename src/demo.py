from braidpy import Braid

"""
To create a braid you have to supply the operations which are needed to create the braid.
In braid theory, these operations are called Artin generators and correspond to the crossings of two strands.
Let's start by taking a 3 strands braid and let's consider we have them attached at the top of the screen and hanging below.
The first strand (1) is on the left, the second strand on the middle (2) and the third strand (3) on the right.

We know consider the first operation where we are going to take the first strand (1) and move it above the next neightboor (2) (to the right)
Programmatically this is coded as follows, where the 1 means we are taking the first strand,
and the sign + means we are moving it above its neighboor (the next one on the right):
"""
first_upcrossing = Braid([+1], n_strands=3)
print(first_upcrossing)
first_upcrossing.draw()
first_downcrossing = Braid([-1], n_strands=3)
print(first_downcrossing)
first_downcrossing.draw()
first_downcrossing_inverted = first_upcrossing.inverse()
print(first_upcrossing, "inverted gives also:", first_downcrossing_inverted)
first_downcrossing_inverted.draw()
