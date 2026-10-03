# Solving a braid's shape numerically

[Why a braid's shape has no closed form](why_no_closed_form.md) argues that a
braid word does not map to a tightened shape by any formula. That rules out an
analytic answer; it does not rule out an answer.

This page states the numerical problem worth posing if this is picked up
again — the variables, the objective, the constraints, the method, where to
start it, and how to tell whether it worked. Nothing here is implemented in
braidpy. It is a specification, not a description.

---
## The problem to pose

### Variables

Each strand as a periodic curve, discretised however suits the solver — say
*m* points per strand per period, or a Fourier truncation if smooth curves are
wanted for free. Fourier is a reasonable basis *for representing* the answer
even though it does not deliver it.

### Objective

- **Total length** Σᵢ ∫ |rᵢ′| — the right objective for limp yarn pulled
  tight, which is most braids and all rope.
- **Length + bending**, Σᵢ ∫ (T|rᵢ′| + B κᵢ²) — for cord, wire or anything
  with stiffness of its own. The ratio √(B/T) is a length: how far bending can
  resist tension, and therefore how sharply a strand may turn. It is the one
  number that decides whether a braid looks taut or lazy.

Minimising per strand independently is not enough. The strands are coupled
through the contact constraint, and it is the contact that sets the braid's
size — so it is one problem over all *n* strands, not *n* problems.

### Constraints

- **Periodicity and the permutation**: rᵢ(L) = r_σ(i)(0), σ from the word.
- **Non-interpenetration**: |rᵢ(z) − rⱼ(z)| ≥ d, enforced at the
  discretisation points.
- **Topology**: *not* as a constraint. Enforce it by starting inside the right
  class and never letting a crossing pass through a strand. Non-interpenetration
  does that on its own if the steps are small enough: two curves cannot swap
  sides without passing through each other. So a feasible descent path from a
  correctly braided start stays correctly braided — which makes the initial
  guess part of the specification rather than a convenience.

### Method

Active-set contact iteration is the obvious first thing: solve with the
currently touching pairs held at exactly *d*, find new violations, add them,
repeat. Each iteration is a smooth problem. Alternatively a barrier or penalty
on the separation, which is easier to implement and harder to trust near
contact.

Expect local minima. Report which one you found rather than calling it *the*
shape.

### The initial guess

The drawn geometry in `parametric_strand.strand_paths` — strands stepping
between slots along a profile, lifting over and dipping under — is a good
starting configuration. It is in the right braid class by construction, and it is
cheap. That is its honest use: not a shape, a starting point.

### How to know it worked

Three checks, all already in the package or its tests:

1. **Closest approach equals the diameter.** If it is larger, the braid has
   not finished tightening. If it is smaller, the shape is not physical at all
   and nothing else about it matters.
2. **Total length decreases monotonically** as the solver iterates, and
   converges under refinement of the discretisation.
3. **The rope limit.** Run the solver on a word of turns with no crossings
   and it must reproduce plain helices at the radius `lay_radius` finds for
   that lay — *not* the packing radius d/(2 sin(π/n)), which is only the limit
   of no lay at all — see [The shape of a laid rope](laid_rope.md). It is the
   case with a known answer, so it is the
   test that can catch a solver that is confidently wrong. Get it to agree
   with `packing_radius` as the lay is stretched out, too: that is a second
   known point, and a free one.

---
## A first, restricted version: a braid as it is made

`braidpy.take_off` poses a restricted form of this problem for a braid as it
comes off whatever made it, and solves it. All it needs is where each strand's
carrier was, in a plane, over time (`take_off.StrandTrajectories`), and
several things can say that:

- a horn gear machine, through `horn_gear.take_off.carrier_trajectories`;
- a parametric braid, through `take_off.parametric_trajectories`, and so a
  braid word, through `take_off.braid_word_trajectories` — anything that
  makes a word can be laid, kumihimo sequences included;
- strands moved between the slots of a disk, through
  `take_off.disk_trajectories`; a mobidai's configuration through
  `take_off.mobidai_trajectories`, and a kumihimo sequence through
  `take_off.kumihimo_trajectories`. A strand that moves while the others stay
  passes over them — over as seen from above the disk, where the braider
  works, with the braid going down through the middle — which is *inside*
  the rim. Read in slot order, inside as over, that gives the crossings the
  mobidai and the kumihimo write down for themselves. It is the opposite way
  round from `annulus_braid`, which looks at a tube from outside.

From there it is the same for all of them:

- **The initial guess** is the source itself: each yarn lies over the path its
  carrier traced, lifted along the axis by the braid taken off since
  (`take_off.lay_yarns`). It is in the right braid class by construction, which is
  what this page asks of a start.
- **Drawing in.** The braid is formed on a fell — a circle, or a braiding
  point — and is the carrier footprint scaled toward the axis by a factor *k*.
  Scaling the plane at fixed height cannot pass one yarn through another, so
  every *k* > 0 keeps the topology. Given a yarn diameter, the smallest *k*
  with no two yarns closer than *d* has a closed form over the samples
  (`take_off.jammed_contraction`): for two samples a height *dz* apart and *s* apart
  sideways, *k* = √(*d*² − *dz*²) / *s*, and the braid jams at the largest.
- **The fell is only a boundary.** A fell circle, or a braiding point, sets
  the size where the braid starts; a short distance above it the braid is
  drawn to its jammed size instead, by a scale that varies with height. Any
  positive scale at each level keeps the topology, so how it varies does not
  matter.
- **Tightening** (`take_off.tighten_yarns`) minimises length with
  each sample held at its height — the small-slope form of the length
  objective — and enforces non-interpenetration by pushing apart any two
  samples of different yarns closer than *d*. The tension is integrated
  implicitly (one backward-Euler step along the curve-shortening flow per
  iteration, the matrix inverted once), which settles a yarn in tens of
  iterations rather than thousands, but no sample moves more than *d*/5 per
  iteration, so a feasible path from the start stays in the same braid
  class, as argued above. The yarn is held at the fell and at its oldest end.

The check that matters is that the result does not depend on the start. Far
enough from the fell, a braid made at a braiding point, at the jammed fell,
or at a fell twice that size tightens to the same cross-section — and a flat
braid comes out as a ribbon (nine carriers: about 4.6 *d* wide by 1.8 *d*
thick) while a tubular one stays round. And laying a braid word, drawing it
in and tightening it, then reading the word back off the yarns, gives the
word it started from — less any crossing that undoes itself, which tension
pulls out. Both are in the tests.

What it does not yet do: let samples move along the axis, which a full length
minimisation would; bending stiffness; periodicity, rather than holding both
ends; and the check against the rope limit.

### Another approach: beads on springs

The braid simulator at craftdesignonline.com (braid3d) models each thread
as a chain of beads one unit apart, joined by springs, with beads of
different threads repelling inside a contact distance and a weight pulling
each thread toward its bobbin. The beads move freely in three dimensions and
are relaxed from a queue, so it gets axial sliding for free — the first
thing missing above. Its price is a step size that has to be kept small for
stability, where the implicit step here does not.
