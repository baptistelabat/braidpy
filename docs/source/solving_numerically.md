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
