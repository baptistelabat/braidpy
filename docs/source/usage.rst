Usage
=====

.. _installation:

Installation
------------

To use braidpy, first install it using git:

.. code-block:: console

 git clone git@github.com:baptistelabat/braidpy.git
To install the required dependencies, follow the steps below:

1. Install `uv` by following the official [installation guide](https://docs.astral.sh/uv/getting-started/installation).
2. Alternatively, run the command from root of repository:
   ```bash
   cd braidpy
   make install-uv

Launching demo (in progress)
----------------

```
Alternatively, if you have make install, just run:
```bash
make demo
```

To create a braid you have to supply the operations which are needed to create the braid.
In braid theory, these operations are called Artin generators and correspond to the crossings of two strands.
Let's start by taking a 3 strands and let's consider we have them attached at the top of the screen and hanging below.
The first strand (1) is on the left, the second strand on the middle (2) and the third strand on the right.

We know consider the first operation where we are going to take the first strand and move it above the next neightboor (to the right)
Programmatically this is coded as follows, where the 1 means we are taking the first strand,
and the sign + means we are moving it above its neightboor (the next one on the right)
first_step = Braid([+1], n_strands=3)

Alternatively, we could move the first braid below its neighboor. For this we change the sign
first_step = Braid([+1], n_strands=3)

The next step, would be to move the third braid above the (new) middle one.
We we exchange the position of two braids, the index always correspond to the one the more on the left.
So here instead of saying that we move the third strand above the second, we say that we move the second below third,
which is equivalent
second_step = Braid([-2], n_strands=3)

We have now our two basic operations.
We can combine them in different ways.

One is to list the different operations:
b = Braid([1, -2], n_strands=3)

The second one is to use the multiplication symbol.

b= first_step * second_step

We obtain the following braid:
1 2 3
1>2 3
2 1<3
2>3 1

