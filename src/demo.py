from braidpy import Braid

print(
    """
To create a braid you have to supply the operations which are needed to create the braid.
In braid theory, these operations are called Artin generators and correspond to the crossings of two strands.
Let's start by taking a 3 strands braid and let's consider we have them attached at the top of the screen and hanging below.
The first strand (1) is on the left, the second strand on the middle (2) and the third strand (3) on the right.

We know consider the first operation where we are going to take the first strand (1) and move it above the next neighbour (2) (to the right)
Programmatically this is coded as follows, where the 1 means we are taking the first strand,
and the sign + means we are moving it above its neighbour (the next one on the right):

>>> first_upcrossing = Braid([+1], n_strands=3)
"""
)
first_upcrossing = Braid([+1], n_strands=3)
print(first_upcrossing)
first_upcrossing.draw()
first_downcrossing = Braid([-1], n_strands=3)
print(first_downcrossing)
first_downcrossing.draw()
first_downcrossing_inverted = first_upcrossing.inverse()
print(first_upcrossing, "inverted gives also:", first_downcrossing_inverted)
first_downcrossing_inverted.draw()

print(
    """
The next step, would be to move the third braid above the (new) middle one.
We we exchange the position of two braids, the index always correspond to the one the more on the left.
So here instead of saying that we move the third strand above the second, we say that we move the second below third,
which is equivalent
"""
)
second_crossing = Braid([-2], n_strands=3)
print(
    """
We have now our two basic operations.
We can combine them in different ways.

One is to list the different operations:
"""
)
b = Braid([1, -2], n_strands=3)

print(
    """
The second one is to use the multiplication symbol.
"""
)
basic_step = first_upcrossing * second_crossing


print("""
We obtain the following braid:
1 2 3
1>2 3
2 1<3
2 3 1


To make a longer braid we how have to reproduce the operations.
If wa want a braid where the strands are in the initial order we need to repeat this operation 3 times
This can be done
with

pure_braid = basic_step*basic_step*basic_step
""")
pure_braid = basic_step * basic_step * basic_step

print(
    """
A bure braid is a braid which is changing the order of the strands.

to write this even faster, we can do
pure_braid = basic_step**3
"""
)
pure_braid = basic_step**3
pure_braid.draw()
pure_braid.plot()
