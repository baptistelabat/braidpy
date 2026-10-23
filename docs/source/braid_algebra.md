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

This is the **word problem**, and braidpy answers it two ways:

- `==` compares the braids' Garside normal forms ({doc}`braid_representations`),
  through math-braid (Cha et al., 2001).
- **Handle reduction** (Dehornoy) removes *handles* — a `σᵢ` and a `σᵢ⁻¹`
  (or the other way round) with neither `σᵢ` nor `σᵢ₋₁` between them — until
  none is left; a word is the trivial braid exactly when it reduces to
  nothing ({mod}`braidpy.handles_reduction`). It is fast in practice, though
  no good bound on it is proven.

## Twists and conjugates

- **The half twist** `Δ` turns the whole braid over by half a turn
  (`half_twist()`), and **the full twist** `Δ²` by a whole turn
  (`full_twist()`). The full twist commutes with every braid: it generates
  the centre of the group. `full_twists()` counts how many a braid holds.
- **Conjugates.** `c b c⁻¹` is `b` seen after `c`
  ({func}`braidpy.operations.conjugate`). Conjugate braids close into the
  same knot or link, which is why braids are compared up to conjugacy
  ({func}`braidpy.properties.conjugacy_class`).

## Further

- {doc}`comparing_braids`: whether two braids are alike however written,
  up to conjugacy, repeats and the order of their strands.
- Patrick Dehornoy, *Braids and Self-Distributivity* (Birkhäuser, 2000), and
  his [TressApp](https://dehornoy.lmno.cnrs.fr/Softwares/TressApp/AppletInfo.html),
  which draws the relations.
