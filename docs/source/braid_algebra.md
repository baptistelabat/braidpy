# Braid algebra

Braids on `n` strands form a group, the **braid group** `Bₙ`: braids
multiply by following one with the other, the trivial braid (no crossing)
is the identity, and every braid has an inverse, its mirror image.

```python
from braidpy import Braid

b = Braid([1, -2], n_strands=3)
b * b.inverse() == Braid([], n_strands=3)  # True
b**3  # b followed by itself twice more
```

## Artin's relations

Every braid is a product of the generators `σ₁ … σₙ₋₁` and their inverses,
and two words make the same braid exactly when one can be turned into the
other by these relations (Artin, 1925):

- **Far crossings commute.** `σᵢσⱼ = σⱼσᵢ` when `|i − j| ≥ 2`: crossings of
  four different strands can be done in either order.
- **The braid relation.** `σᵢσᵢ₊₁σᵢ = σᵢ₊₁σᵢσᵢ₊₁`: three strands crossing
  each other once, in two orders, make the same braid.
- And `σᵢσᵢ⁻¹` is no crossing at all.

```python
Braid([1, 3], n_strands=4) == Braid([3, 1], n_strands=4)  # True
Braid([1, 2, 1], n_strands=3) == Braid([2, 1, 2], n_strands=3)  # True
```

## Deciding whether two words are the same braid

This is the **word problem**. `a == b` asks whether `a·b⁻¹` is the trivial
braid (`is_trivial()`), and braidpy answers that two ways:

- **Handle reduction** (Dehornoy) removes *handles* — a `σᵢ` and a `σᵢ⁻¹`
  (or the other way round) with neither `σᵢ` nor `σᵢ₋₁` between them — until
  none is left; a word is the trivial braid exactly when it reduces to
  nothing ({mod}`braidpy.handles_reduction`). It is the faster on most
  braids, but no good bound on it is proven, and on long words of many
  strands it can blow up.
- So it is given a few seconds, and if it has not decided, the braids'
  **Garside normal forms** do ({doc}`braid_representations`), braidpy's own
  ({mod}`braidpy.garside_canonical_form`): the word read with its half twists
  kept at its end, each factor made left-weighted with those before it in one
  pass back. ABOK #3082, 61 strands, against itself rewritten, takes three
  seconds so.

## Shortening a word

A braid has many words, and the shorter is the fewer moves to make, by hand
or on a machine. `braid.shortened()` ({mod}`braidpy.shortening`) gives the
same braid, exactly, in as few crossings as it finds:

- a crossing followed at once by its inverse is taken out;
- a crossing and its inverse kept apart are brought together where the
  braid relations allow: crossings of strands far apart commute, and three
  crossings of three strands can be made the other way round, signs mixed
  too. Each piece of the word is rewritten every way they allow, up to a
  budget, for one where two crossings cancel;
- handle reduction's word is kept if it is shorter, after the same search.
  Removing every handle is not shortening: the book's #3072 has 114
  crossings, and 150 once its handles are reduced.

A word whose crossings all have one sign is as short as it gets, since the
relations keep the sum of a word's signs. A shortest word is not promised:
finding one is hard in general. Braid Studio shows the shorter word under
the braid's own, when it finds one; the catalogue's rectangular braid of 14
goes from 448 crossings to 364.

## Twists and conjugates

- **The half twist** `Δ` turns the whole braid over by half a turn
  (`half_twist()`), and **the full twist** `Δ²` by a whole turn
  (`full_twist()`). The full twist commutes with every braid: it generates
  the centre of the group. `full_twists()` counts how many a braid holds.
- **Conjugates.** `c b c⁻¹` is `b` seen after `c`
  (`c * b * c.inverse()`). Conjugate braids close into the
  same knot or link, which is why braids are compared up to conjugacy
  ({func}`braidpy.properties.conjugacy_class`).

## Further

- {doc}`comparing_braids`: whether two braids are alike however written,
  up to conjugacy, repeats and the order of their strands.
- Patrick Dehornoy, *Braids and Self-Distributivity* (Birkhäuser, 2000), and
  his [TressApp](https://dehornoy.lmno.cnrs.fr/Softwares/TressApp/AppletInfo.html),
  which draws the relations.
