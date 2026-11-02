# Comparing braids

A braid made on a machine, a braid typed as a word and a braid read off a
kumihimo pattern can be the same braid and look nothing alike on paper. The
same braid can be written from another starting point, with far crossings
swapped, made of more or fewer repeats, its strands numbered from the other
side. To say whether two braids are alike — and to suggest, for a braid of your
own, the braids it is most like — the comparison has to be about the braid's
*topology*, not about how it happens to have been written.

{mod}`braidpy.similarity` does so with a **fingerprint**: a few numbers that
do not change however the braid is written, and a distance between
fingerprints.

```python
from braidpy import Braid
from braidpy.similarity import similar

# The plait, typed from its second crossing and repeated five times.
mine = Braid([-2, 1] * 5, 3)
similar(mine, count=3)
# [Match(name='flat3', distance=0.0, same_fingerprint=True), ...]
```

## Deciding it exactly

"The same braid, read from another starting point" is conjugacy in the braid
group, and {mod}`braidpy.conjugacy` decides it: {func}`~braidpy.conjugacy.same_braid`
says yes or no, a proof, where fingerprints only ever prove braids different.

```python
from braidpy.braid import Braid
from braidpy.conjugacy import same_braid

same_braid(Braid([1, -2], 3), Braid([-2, 1], 3))  # True
```

It goes by summit sets (Elrifai and Morton): each braid is cycled to its
*super summit set*, the conjugates as short as any in Garside's normal form,
and that finite set is searched whole; two braids are conjugate exactly when
their sets meet. A first implementation of that conjugated by every
permutation braid, n! of them, and took minutes on 6 and 8 strands. This one
follows only the least permutation braids that keep a braid in the set, at
most one for each crossing σᵢ (Franco and González-Meneses): edo yatsu's
set, 472 braids on 8 strands, is found in about 3 seconds. The set can still
grow exponentially with the strands, so the search stops at a limit and
says so ({class}`~braidpy.conjugacy.SuperSummitSetTooLarge`).

A yes or no does not suggest braids *like* yours: for that, a distance is
wanted, and the fingerprint gives one.

## The fingerprint

It is of the braid's pattern, not its length: the word's repeating unit, and
that unit repeated until every strand is back where it started — the *home*
braid, whose closure makes a loop of each strand.

| | What it says | Tells apart |
| --- | --- | --- |
| strands | how many | |
| loops | the sizes of the loops the unit's closure makes: how it takes the strands round | |
| writhe | the unit's crossings counted with their signs | a braid from its mirror image |
| linking numbers | how many times each two strands wind round each other in a repeat, sorted | how the strands are interlaced |
| Alexander polynomial | of the home braid's closure, sampled on the unit circle | what linking numbers miss |
| Burau polynomial | the characteristic polynomial of the home braid's Burau matrix, sampled on the unit circle | what the Alexander polynomial misses where it vanishes |

None of them changes when the braid is read from another starting point, and
none but the writhe when its strands are numbered from the other side. The
distance adds a share from 0 to 1 for each, 0 for the same fingerprint.

## Why the Alexander polynomial alone is not enough

The Alexander polynomial Δ(t) of a braid's closure is one of the strongest
of the six, and it is computed from the word through the Burau matrix
({func}`braidpy.properties.alexander_polynomial`). But on its own:

| Braid | Δ(t) |
| --- | --- |
| trefoil, σ₁³ | t² − t + 1 |
| its mirror image, σ₁⁻³ | t² − t + 1 |
| two-ply rope σ₁⁸, and twisted the other way, σ₁⁻⁸ | t⁷ − t⁶ + t⁵ − t⁴ + t³ − t² + t − 1 |
| one loop, unknotted, on 1 or 3 strands | 1 |
| three straight strands | 0 |
| the plait (σ₁σ₂⁻¹)⁶ | t¹⁰ − 7t⁹ + … + 1 |

- It does not tell a braid from its **mirror image**: a rope laid S from one
  laid Z. The writhe does.
- It loses the braid itself: it is an invariant of the **closure**, the same
  for braids on different numbers of strands that close up alike (Markov's
  theorem). The number of strands and the loops keep that.
- It **vanishes** for loops that could be pulled apart, and for some links
  that cannot: then it says nothing. Linking numbers still do.
- No handful of invariants is complete: different links can share one.

Linking numbers alone are not enough either: the plait and three strands
hanging straight both have all their linking numbers 0, and the Alexander
polynomial tells them apart.

## The Burau polynomial, where the Alexander polynomial vanishes

The Alexander polynomial of a closed braid is det(1 − B), B the braid's
Burau matrix, up to a factor: the characteristic polynomial det(x − B) of
the matrix at x = 1. Where B has the eigenvalue 1, it is 0, as for many
braids whose closure makes several loops, and it tells nothing apart. The
whole characteristic polynomial does not vanish; like the Alexander
polynomial, it does not change when the braid is read from another starting
point. Sampled at x = 2, on the same circle
({func}`braidpy.properties.burau_polynomial_on_circle`), it tells apart
braids that agree on everything else:

| Braids | Same loops, writhe, linking numbers | Alexander | Burau polynomial |
| --- | --- | --- | --- |
| edo yatsu on a kumihimo disk, ABOK #3070 | yes | 0, both | differ |
| the flat braid of 6, ABOK #3021 | yes | 0, both | differ |

Before the Burau polynomial was in the fingerprint, these were catalogued as
the same braids. It is computed from the eigenvalues of the unit's Burau
matrix, raised to the number of repeats, so that a home braid of thousands
of crossings overflows nothing.

## The Alexander polynomial, sampled

The home braid of a long sinnet is long: ABOK #3048's 85-crossing unit
repeated 60 times. Its polynomial, expanded, takes minutes. Its modulus on the
unit circle, |Δ(e^{iθ})|, is exactly an invariant — on the circle |±tᵏ| = 1,
nothing is left to normalise — and is computed numerically from the unit's
Burau matrix at t = e^{iθ}, raised to the number of repeats
({func}`braidpy.properties.alexander_on_circle`): milliseconds. It matches the
polynomial, where both can be computed, to six digits.

## A catalogue by topology

{mod}`braidpy.topology_catalog` lists braids by what they are rather than by
how they are made. It makes every braid of every other catalogue — braid
words, kumihimo, kumihimo disks, sinnets, braiding machines — and groups those
with the same fingerprint. Each topology points to every way of making it, and
each way back to its topology ({func}`~braidpy.topology_catalog.topology_of`):

```python
from braidpy.topology_catalog import topology_of

plait = topology_of("machine", "flat_3")
[m.key for m in plait.methods]
# ['word:flat3', 'word:inverted_flat3', 'sinnet:abok_2965', 'machine:flat_3']
```

The plait is a braid word, the Dutch braid (the plait seen from behind),
Ashley's #2965 worked on his stand, and what a three-carrier flat braiding
machine makes. For a braid of your own,
{func}`~braidpy.topology_catalog.related` gives the topologies nearest it, and
with each the ways to make it.

A disk braid that creeps round the disk from cycle to cycle, as kongo gumi
does, is fingerprinted over as many cycles as bring every strand home, not
its first. A machine braiding round cores has no braid word of its strands
alone, and is left out. Making every braid takes some ten seconds, so the
catalogue is built once, when first asked for.

Braid Studio shows it beside every braid it makes: **Also made as**, the
other ways of making the same braid, and **Nearest braids**. The catalogue
is made with the site, as JSON ({func}`~braidpy.topology_catalog.export`),
and read back in the browser ({func}`~braidpy.topology_catalog.load`);
{func}`~braidpy.topology_catalog.for_page` finds a catalogue's braid by its
description, and any other by the fingerprint of the braid made.

## Limits

- **Equal fingerprints do not prove two braids the same.** Different ones
  prove them different; {func}`~braidpy.conjugacy.same_braid` proves either.
- **A braid seen from behind is the same braid.** The Dutch braid,
  σ₁⁻¹σ₂, is the plait σ₁σ₂⁻¹ with its strands numbered from the other side,
  and has its fingerprint.
- **The distance's weights are a choice**: each part counts the same.

## References

- W. Burau, "Über Zopfgruppen und gleichsinnig verdrillte Verkettungen",
  *Abh. Math. Sem. Hamburg* 11, 179 (1935): the Burau matrix, and the
  Alexander polynomial of a closed braid from it.
- J. W. Alexander, "Topological invariants of knots and links", *Trans. Amer.
  Math. Soc.* 30, 275 (1928).
- D. Rolfsen, *Knots and Links* (Publish or Perish, 1976): Alexander
  polynomials, linking numbers, the tables checked against.
- J. S. Birman, *Braids, Links, and Mapping Class Groups* (Princeton, 1974):
  closed braids, and Markov's theorem.
- E. A. Elrifai and H. R. Morton, "Algorithms for positive braids", *Quart. J.
  Math.* 45, 479 (1994): conjugacy, decided exactly.
- N. Franco and J. González-Meneses, "Conjugacy problem for braid groups and
  Garside groups", *J. Algebra* 266, 112 (2003): the super summit set found
  through minimal simple elements.
- J. González-Meneses, "The nth root of a braid is unique up to conjugacy",
  *Algebr. Geom. Topol.* 3, 1103 (2003): why braids repeated as often can be
  compared by what is repeated.
