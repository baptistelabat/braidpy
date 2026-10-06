# Comparing two braids

A braid made on a machine, a braid written as a word and a braid read off a
kumihimo pattern can be the same braid and look nothing alike on paper. To say
whether two methods make the same thing, the comparison has to be about the
braid, not about how it happens to have been written down.

Three different questions hide behind "are these the same braid?", and they
need different answers.

| Question | Relation | Settled by |
| --- | --- | --- |
| Do these two words spell the same braid? | equality in $B_n$ | left normal form, or handle reduction |
| Is one the other read from a different starting point? | conjugacy in $B_n$ | summit sets |
| Do they close up to the same link? | Markov equivalence | not implemented here |

## Why the word is not enough

The same braid has many words. Generators far apart commute,

$$\sigma_i \sigma_j = \sigma_j \sigma_i \qquad |i - j| \ge 2,$$

and neighbouring ones satisfy the braid relation,

$$\sigma_i \sigma_{i+1} \sigma_i = \sigma_{i+1} \sigma_i \sigma_{i+1}.$$

So $\sigma_1\sigma_2\sigma_1$ and $\sigma_2\sigma_1\sigma_2$ are one braid written
two ways. Any comparison made on the letters alone will call them different.

## Starting somewhere else is conjugation

A braid off a machine repeats, and where the repeat is cut is arbitrary: the
same pattern read from the next step along is the same braid once it has been
going for a while. Writing the word as $w = a\,b$, reading it from one step
later gives

$$b\,a = a^{-1} (a\,b)\, a,$$

which is $w$ conjugated by $a$. So "the same up to where you start reading" is
**conjugacy in the braid group**, and that is the relation
{mod}`braidpy.braid_conjugacy` decides.

## The least rotation, and why it is not the answer

A natural idea is to rotate the word until it reads smallest: take the lowest
first index, and where several tie, prefer the one whose next index is lower,
and so on. That is the **lexicographically least rotation** of a cyclic word,
and it is the standard canonical form for a necklace. Booth's algorithm finds
it in linear time, and `braidpy.braid_conjugacy.least_rotation` implements it.

It is a canonical form for a *word*, not for a *braid*. Because
$\sigma_1\sigma_2\sigma_1$ and $\sigma_2\sigma_1\sigma_2$ are the same braid but
no rotation of one is the other, their least rotations differ. It is useful as
a cheap first test and for comparing words as words; it cannot decide braids.

## Normal form solves the other problem

Artin's left normal form writes a braid as

$$\Delta^{p} A_1 A_2 \cdots A_r,$$

with $\Delta$ the half twist and each $A_i$ a permutation braid, left-weighted
against the next. It is unique, so it decides equality:
{mod}`braidpy.garside_canonical_form` gives the same answer for
$\sigma_1\sigma_2\sigma_1$ and $\sigma_2\sigma_1\sigma_2$, and for
$\sigma_1\sigma_3$ and $\sigma_3\sigma_1$.

It does **not** decide conjugacy. Rotating a word generally changes its normal
form, as it must: normal form is a property of the element, and conjugate
elements are different elements.

Removing the $\Delta^{p}$ does not repair this. The half twists are part of the
braid, and dropping them gives a different braid. What is true is that $p$ and
$r$ survive conjugation, which is useful in another way.

## What conjugate braids must agree on

Three numbers are the same for every braid in a conjugacy class:

- `inf`, the exponent $p$ of the half twist in front,
- `canonical_length`, the number of factors $r$,
- `sup`, their sum $p + r$.

Braids differing in any of them cannot be conjugate, so they are a cheap way to
say *no* before searching. They are not a complete invariant: braids can agree
on all three and still not be conjugate, so agreement decides nothing on its
own.

## Cycling, decycling and the summit

Conjugating moves a braid around its class; the class is infinite, but the
elements of it with the largest `inf` and the smallest `sup` form a finite set
— the **super summit set**. Two braids are conjugate exactly when their super
summit sets are equal, and it is enough to compare one element of each if the
element is chosen the same way.

Two operations drive a braid there. **Cycling** moves the first canonical
factor to the back; it never lowers `inf` and sooner or later raises it as far
as it will go. **Decycling** moves the last factor to the front; it never
raises `sup`. Applied in turn until neither moves, they land on a summit
element.

Neither necessarily helps on the first go: `inf` can sit still for several
cyclings before it rises. Stopping at the first that does not help leaves some
braids short of their summit, and gives them a canonical form of their own —
which is a real bug this implementation had, and what the randomised test in
`tests/test_braid_conjugacy.py` was written to catch.

From a summit element the rest of the set is reached by conjugating by
permutation braids, and the smallest element of the set, under a fixed order,
is the canonical name of the whole class.

```python
from braidpy.braid_conjugacy import are_conjugate, canonical

word = [1, -2, 1, -2, 1, -2]
offset = word[1:] + word[:1]

are_conjugate(word, offset, n_strands=3)      # True
canonical(word, 3) == canonical(offset, 3)    # True
```

## What this does not do

**Faster summit sets.** The super summit set is the first of three. The
**ultra summit set** (Gebhardt) keeps only the elements lying on a closed
cycling orbit, and the **set of sliding circuits** (Gebhardt and
González-Meneses) is smaller again. Both are considerably faster on long
braids. The implementation here closes the super summit set by conjugating
with every permutation braid, which is correct and plain but grows quickly
with the number of strands; it raises `TooManyConjugates` rather than grinding.

**Different numbers of strands.** Conjugacy compares braids on the same $n$.
Braids on different numbers of strands that close to the same link are related
by Markov moves — conjugacy together with stabilisation — which is a harder
problem and not attempted here.

**The centre.** If two methods differ by a full twist $\Delta^{2}$, which is
central, they are genuinely different braids and this will say so. Quotienting
by the centre is a reasonable thing to want, but it is a different equivalence
and should be asked for deliberately rather than reached by discarding the
twist.

**The annulus.** A braid on a machine lives on a cylinder, and turning the
whole machine by one carrier is a symmetry of the pattern as well. Comparing in
the affine braid group would catch that; see {mod}`braidpy.annulus_braid`.

## References

Garside theory and the conjugacy problem:

- Garside, F. A. (1969). The braid group and other groups. *Quarterly Journal
  of Mathematics*.
- Elrifai, E. A., and Morton, H. R. (1994). Algorithms for positive braids.
  *Quarterly Journal of Mathematics*. Cycling, decycling and the super summit
  set.
- Birman, J. S., Ko, K. H., and Lee, S. J. (1998). A new approach to the word
  and conjugacy problems in the braid groups. *Advances in Mathematics*.
- Gebhardt, V. (2005). A new approach to the conjugacy problem in Garside
  groups. *Journal of Algebra*. The ultra summit set.
- Gebhardt, V., and González-Meneses, J. (2010). The cyclic sliding operation
  in Garside groups. *Mathematische Zeitschrift*. The set of sliding circuits.
- Dehornoy, P., Digne, F., Godelle, E., Krammer, D., and Michel, J. (2015).
  *Foundations of Garside Theory*. European Mathematical Society.
- González-Meneses, J. (2011). Basic results on braid groups. *Annales
  mathématiques Blaise Pascal*. A readable way in.

Deciding equality:

- Dehornoy, P. (1997). A fast method for comparing braids. *Advances in
  Mathematics*. Handle reduction; see {mod}`braidpy.handles_reduction`.

Cyclic words:

- Booth, K. S. (1980). Lexicographically least circular substrings.
  *Information Processing Letters*.
- Duval, J.-P. (1983). Factorizing words over an ordered alphabet. *Journal of
  Algorithms*. Lyndon words, the same canonical form by another route.

Closed braids and links:

- Birman, J. S. (1974). *Braids, Links, and Mapping Class Groups*. Princeton
  University Press. Markov's theorem.
