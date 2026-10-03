# Why a braid's shape has no closed form

This page records why braidpy stops where it does on analytic geometry. It was
written after several attempts to go further failed, each in a different way,
and it is meant to save the next person those attempts.

The question is: given a braid word, is there a closed-form expression for the
shape the strands take when the braid is pulled tight?

The short answer is no, except in symmetric special cases, and the reasons are
not about effort or cleverness. They are properties of the problem.

Closed form being out does not mean the problem is ill-posed. A numerical
statement of it that would be worth solving is set out in
[Solving a braid's shape numerically](solving_numerically.md).

---

## 1. What "the shape" means

A braid of *n* strands is *n* curves **r₁(z) … rₙ(z)**, each running along the
axis *z* over one period *L*, each closing up: **rᵢ(L) = r_σ(i)(0)** for the
permutation σ the word performs.

Pulled tight by an axial force, with the strands treated as inextensible and
of diameter *d*, the shape is whatever solves

> **minimise** Σᵢ ∫₀ᴸ |rᵢ′(z)| dz — the total length of yarn
>
> **subject to**
> 1. the curves realise the braid word (topology), and
> 2. |rᵢ(z) − rⱼ(z)| ≥ d for every pair *i ≠ j* and every *z* (nobody occupies
>    anybody else's space).

Add a bending term ∫ κ² if the strands are stiff rather than limp. Nothing
below changes if you do.

This is the right problem. Every difficulty is in the constraints.

---

## 2. Why there is no closed form

### 2.1 The topology constraint is not an equation

Constraint 1 is a statement about which *homotopy class* the family of curves
lies in. There is no way to write "this set of curves belongs to braid class β"
as a system of equalities or inequalities on coordinates or on Fourier
coefficients. It is a discrete label on a connected component of the
configuration space, not a level set of any function.

The usual dodge is to pin the curves to specific points — strand 2 is *here*
at step 3 — which does turn topology into equations. But those points are a
drawing convention, chosen by whoever draws the braid diagram. Pin them and
you have not solved for the shape; you have asserted most of it and solved for
the wiggles in between. That is what an earlier version of this package did,
and it is the single biggest way to fool yourself here.

### 2.2 The non-interpenetration constraint is non-convex

|rᵢ(z) − rⱼ(z)| ≥ d requires the separation vector to lie *outside* a ball.
The complement of a ball is not convex, so the feasible set is not convex, so
the problem has no unique minimum and no first-order condition that
characterises the answer. Different starting configurations settle into
genuinely different shapes, all locally optimal.

### 2.3 It is an infinite family of constraints

The separation must hold at *every* height *z*, not at finitely many. That
makes it a semi-infinite programme. Discretise *z* and you get a finite
problem, but then you have chosen a discretisation and left closed form
behind.

### 2.4 The contact set is part of the unknown

In the solution, some strands touch — the separation is exactly *d* — over
some intervals of *z*, and are clear elsewhere. Which pairs touch, and where,
is not known in advance. It is a combinatorial choice, and there are many
possibilities. A closed-form answer would have to be a formula whose form
depends on a combinatorial object nobody can name before solving.

This is the deepest of the four. Even if 2.1–2.3 were waved away, you would
still need to guess the contact set to write anything down.

### 2.5 Length is not a quadratic functional

∫|r′| dz is not quadratic, so minimising it is not a linear solve. It becomes
quadratic under the small-slope approximation

> ∫ √(1 + f′²) dz ≈ L + ½ ∫ f′²

which is what makes the Fourier approach tempting — that functional *is*
diagonal in a Fourier basis, and minimising it under linear equality
constraints is one linear system. But a braid strand crossing one slot per
unit of axis has a slope of order one, not a small one. Measured on the
three-strand flat braid, the approximation overstates the excess length by
about **22%**. It overstates it by a consistent 22%, so it ranks shapes
correctly, and it is a perfectly good *smoother*. It is not the length.

### 2.6 This is a known hard problem under another name

Finding the shortest curve of given thickness in a prescribed knot or link
class is studied as **ropelength** or the **ideal knot** problem. It is solved
numerically, and the problem is open for every non-trivial knot: the unknot is
the only one whose ideal shape is known explicitly, and all others have been
approximated numerically only. The trefoil's ropelength, after decades of
computation, is an estimate — about 32.74 — rather than a value anyone has
written down. A tight braid is the same problem with a braid class instead of a
knot class and periodic boundary conditions instead of a closed loop.

See [Ropelength](https://en.wikipedia.org/wiki/Ropelength) for the state of the
problem, and [High resolution portrait of the ideal trefoil
knot](https://arxiv.org/pdf/1402.5760) for how far numerical work has got on the
simplest non-trivial case.

---

## 3. Where closed form does survive

It survives where symmetry removes the two hard parts — where the shape family
has few enough parameters to write down, and where symmetry names the contact
set without a search. Then the open problem becomes a small optimisation, and
that is a real answer even though it is not a formula.

### 3.0 A bound for braids that are one curve repeated

This one applies to a *class* of braids, not to all of them, and the class is
worth naming precisely before the bound is stated.

Call a braid **uniform** when every strand does the same thing a fraction of a
period later — when strand *k*'s centreline is

> **r_k(z) = ( c(z − kP/n), z )**

for one shared cross-section curve **c** of period *P*. The strands are one
curve, repeated at *n* phases. A laid rope is uniform. So is the figure-eight
plait of §3.2, and so is a regular maypole braid. An arbitrary braid is not —
one strand running straight up the middle while the others weave around it is
a braid, and nothing here applies to it.

For a uniform braid, take any height *u* on strand *a* and look at strand *b*
at height *u + (b−a)P/n*:

| | cross-section | height |
|---|---|---|
| strand *a* at *u* | c(u − aP/n) | u |
| strand *b* at *u + (b−a)P/n* | c(u − aP/n) | u + (b−a)P/n |

The cross-section arguments are *identical*. Those two points are at the same
place across the braid and differ only in height, by (b−a)P/n. With
neighbouring phases:

> **two strands have points exactly P/n apart, however wide the braid is
> made** — and therefore **P ≥ n·d**.

Widening the braid does not help, because the two points are the same point of
the same curve and move together. Physically: a strand passes through every
cross-section position its neighbour does, just later, and the only thing
separating them there is how much axis went by in between.

Two caveats. The bound is **not attained** — at P = n·d exactly, clearing *d*
would need that approach to be the only close one, which takes an infinite
radius, so `lay_radius` refuses a lay at or below it. And it is usually **not
the binding constraint**: crowding across the cross-section bites first, and
the figure-eight family runs out between 6·d and 7·d of period, not at 3·d.
`minimum_lay` and `minimum_period` are this bound, and neither promises more.

Its other use is to demolish a tempting shortcut. Comparing strands **at the
same height** is much cheaper than comparing every pair of heights, and it is
wrong for exactly the reason above: the close approach is between points at
*different* heights. On a three-strand rope laid one turn per period, the
equal-height figure says the clearance is 0.40 of a diameter when it is really
0.27. `closest_approach` compares every pair of heights.

### 3.1 A laid rope

*n* strands winding together, no crossings. Each strand is a helix, so the
family has one parameter — the radius — and symmetry says which strands touch
without anyone having to search for it. Because the strands are one curve
repeated, their separation reduces to a single variable and the clearance is
exact.

What it does not reduce to is a formula. Locating the minimum of that
clearance means solving a transcendental equation, so `lay_radius` bisects on
the exact clearance instead, and the familiar packing radius d/(2 sin(π/n))
turns out to be only its zero-lay limit — `packing_radius` is labelled as
such.

[The shape of a laid rope](laid_rope.md) carries the clearance function, the
equation that has no closed-form root, and the figures.

### 3.2 The classic three-strand flat braid

Given as equations rather than derived here:

> x_k(z) = A sin(2πz/P − 2πk/3)  
> y_k(z) = H sin(4πz/P − 4πk/3)

The over-and-under runs at exactly twice the frequency of the side-to-side, so
each strand is a figure eight in cross-section and the three of them are that
one figure at three phases. `braid_word` reads the braid straight off the
curves — six crossings to the period, (σ₁σ₂⁻¹)³ — so the family is confirmed
to be the braid it claims to be rather than assumed to be.

Two amplitudes and a period are all that is left, so the shape can be
*optimised*: shortest strands that still clear a diameter. Within the
cross-section alone there is even a closed form — two strands pass a crossing
at ±H√3/2, so they clear H√3 there, and that is the tightest spot in the
cross-section exactly when **A ≥ 2H**, which falls out of minimising
3(A²c² + H²(2c² − 1)²). Counting the axial offset as well, it is a
two-variable search, `tightest_figure_eight`.

What it finds, for strands of diameter *d*:

| period | A | H | A/H | strand per unit of braid |
|---|---|---|---|---|
| 6·d | — | — | — | no shape of this family fits |
| 8·d | 0.91·d | 0.75·d | 1.21 | 1.383 |
| 9·d | 0.94·d | 0.69·d | 1.37 | 1.285 |
| 20·d | 1.02·d | 0.60·d | 1.70 | 1.060 |

The family runs out between six and seven diameters of period — well before
the *3d* of §3.0, because crowding in the cross-section bites first.

### 3.3 A braided tube

Published, not derived here: *The geometry of tubular braided structures*,
page 19 —
<https://scispace.com/pdf/the-geometry-of-tubular-braided-structures-32b4yiwio2.pdf>.
A strand winds round the tube at a fixed angle to the axis while its distance
from the axis swings in and out. That swing is the braid: take it away and the
strands are helices that would have to pass through one another.

Unlike the rope, the narrowest workable radius **is** available in closed
form:

> **R = b · max( √(1 + n²/4), (n/2)·tan q )**

and why it closes is the part that belongs to this argument rather than to the
tube. A crossing is a point of symmetry for *both* strands, so it is
automatically a critical point of the distance between them and only the
second-order terms decide — which is algebra. Two helices of a rope have no
such point, and locating their nearest approach is the transcendental problem
of §3.1. Symmetry does the work in both cases; here there is enough of it, and
there there is not.

One limitation belongs here too, because it bears on what closed form is
worth: the model cannot make a *tight* tube. At the narrowest radius that does
not crowd, the strands hide between 0.35 and 0.45 of the surface whatever the
strand count or braid angle. A shape available in closed form is not therefore
a realistic one.

[The shape of a braided tube](braided_tube.md) gives the curve, the two
placement rules the published formula leaves unsaid, the derivation of the
radius, the crossover between its two conditions and the cover limitation,
with figures.

### 3.4 What had to be true

In all three: a family with two or three parameters, and a symmetry that says
which strands touch. A braid with irregular crossings has neither, and
nothing above transfers to it.

Notice also what none of the three gives you. Each is a *family* someone
wrote down, with the parameters then chosen by search. None is derived from
the braid word, and none would tell you the shape of a braid nobody has
already found the family for. That is §2, and it has not moved.

## 5. What is in the package, and what it is for

Kept, because each is verified and none of it claims to be a physical shape:

- `braid.Braid.slot_history` and `parametric_strand.strand_paths` — braid word
  → which slot each strand is in, and which side of each crossing it took.
  Exact combinatorics. The drawn curve agrees with braidpy's existing
  `Braid.to_parametric_strands` to 5·10⁻¹⁶, so it is that drawing written in
  closed form, not a second convention.
- `pure_braid` — whether a word closes, and how many repeats make it, which
  is what decides whether a strand's path has a period at all.
- `annulus_braid.py` — the ring's move vocabulary and bookkeeping, the exact
  helix clearance, and the rope's shape from §3.1.
- `symmetric_braid.py` — the figure-eight family of §3.2, its clearance, the
  search within it, and `braid_word`, which reads a braid off a set of curves
  so a shape can be checked rather than believed.
- `parametric_strand.arc_length` and `parametric_braid.closest_approach` —
  measurements, which work on any shape from any source, including a
  solver's.
- `parametric_strand.tube_mesh` and `tube_faces`, and
  `ParametricBraid.plot(tube_diameter=...)` — drawing strands at their real
  thickness, so that whether they touch can be seen rather than believed.

`src/braidpy/analytic/` holds nothing but a pointer to this page: the
directory is named for the thing that turned out not to exist, and keeping it
seemed better than pretending the question was never asked.

Removed, because it asserted more than it established: a constrained
minimiser whose constraints pinned every strand to its slot at every step, and
a tubular shape whose crossings were held open at a single point and which
consequently had its strands overlapping by a third of a diameter. Both looked
like physics and were not. Their epitaph is §2.1.
