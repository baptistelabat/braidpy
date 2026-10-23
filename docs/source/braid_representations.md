# Braid representations

A braid can be written down many ways. braidpy reads and writes each of
these, and moves between them.

## A braid word

A braid on `n` strands is written as its crossings in order, each an Artin
generator: `σᵢ` crosses the strand in place `i` over the one in place
`i + 1`, `σᵢ⁻¹` under ({doc}`usage`). braidpy keeps a braid as the list of
signed indices, `Braid([1, -2], n_strands=3)` for `σ₁σ₂⁻¹`, and writes it in
the usual notations:

| Notation | `σ₁σ₂⁻¹` | Written by | Read by |
|---|---|---|---|
| Signed indices | `1 -2` | `generators` | `Braid([...])`, `parse_word` |
| Greek | `σ₁σ₂⁻¹` | `format()` | `parse_word` (also `s1 s2^-1`) |
| Letters | `aB` | `format_to_notation("alpha")` | `parse_word` |
| LaTeX | `s_{1}^{1.0} s_{2}^{-1.0}` | `format_to_notation("artin")` | |
| math-braid, braidlab | `<1 : -2>` | `format_to_notation()` | |

In letters, `a` is `σ₁`, `b` is `σ₂` and so on; a capital is the inverse.

## Where the strands go

A braid takes the strand starting in each place to a place at the other end:
its **permutation**. `perm()` gives where each strand ends, and
`permutations()` the order of the strands after each crossing:

```python
Braid([1, -2], n_strands=3).perm()   # [2, 3, 1]
```

A braid whose permutation is the identity is **pure**
({mod}`braidpy.pure_braid`). Many words share a permutation; the
permutation forgets which strand passed over.

## A matrix

The **Burau representation** sends each generator to a matrix in a variable
`t`, and a braid to the product of its generators' matrices
(`to_matrix()`, `to_reduced_matrix()`). Equal braids have equal matrices;
the reduced matrix gives the closure's **Alexander polynomial**
({func}`braidpy.properties.alexander_polynomial`), an invariant of the knot
or link the braid closes into.

## A normal form

Of all the words making a braid, the **Garside normal form** picks one: a
power of the half twist `Δ`, then a sequence of permutation braids, each as
long as it can be ({mod}`braidpy.garside_canonical_form`,
`get_canonical_factors()`). Two words make the same braid exactly when their
normal forms are equal.

## A shape in space

A braid word says nothing of a braid's shape; braidpy lays one for it.
`to_parametric_strands()` gives each strand as a curve, crossing over or
under where the word says, for a 3D view ({doc}`visualization`). How a
braid's yarns settle into their real shape is the subject of
{doc}`rope_physics` and {doc}`why_no_closed_form`.

## A way of making it

A braid is also what a kumihimo disk's moves, a braiding machine's carriers,
a lace machine's punchcard or a sinnet on Ashley's stand make. braidpy reads
the braid word off each, and goes back from a braid to each
({doc}`bridges`).
