# Getting started

Install braidpy as the [home page](index.md) says, with its `viz` extra to
draw braids. Then a braid is a few lines away.

## A braid, crossing by crossing

A braid is written as a **braid word**: its crossings in order, each an
**Artin generator**. `σᵢ` crosses the strand in place `i` over the strand
in place `i + 1`; `σᵢ⁻¹` crosses it under. braidpy writes `σᵢ` as `i` and
`σᵢ⁻¹` as `-i`. On three strands, left to right:

```python
from braidpy import Braid

over = Braid([1], n_strands=3)  # σ₁: the left strand crosses over the middle one
under = Braid([-1], n_strands=3)  # σ₁⁻¹: under, the inverse of σ₁
under == over.inverse()  # True
```

The inverse of a braid is its image in a mirror: its crossings in the other
order, each the other way.

`draw()` draws a braid in the console, a line per crossing, the arrow
pointing from the strand passing over:

```python
over.draw()
```

```
1 2 3
1>2 3
2 1 3
```

## Words, notations, products

A braid can be given as a list or read from text, in any of the usual
notations, and written back in another:

```python
from braidpy.braidword import parse_word

b = Braid([1, -2], n_strands=3)
Braid(parse_word("s1 s2^-1"), n_strands=3) == b  # True: σ₁σ₂⁻¹
Braid(parse_word("aB"), n_strands=3) == b  # True: a is σ₁, B is σ₂⁻¹
b.format()  # 'σ₁σ₂⁻¹'
b.format_to_notation("alpha")  # 'aB'
```

Braids multiply by following one with the other, and a power repeats one:

```python
step = over * Braid([-2], n_strands=3)  # the same braid as b
plait = step**3  # three steps of the plait
```

## Pure braids

Three steps of the plait bring every strand back to where it started:

```python
plait.draw()
plait.is_pure()  # True
plait.perm()  # [1, 2, 3]: where each strand ends
```

A braid that brings every strand home is **pure**. A pure braid closes into
as many loops as it has strands; any braid closes into a knot or a link
whose loops are its permutation's cycles.

## Same braid, different words

Two words can make the same braid: `σ₁σ₂σ₁` and `σ₂σ₁σ₂` do, by Artin's
relations ({doc}`braid_algebra`). `==` compares braids, not words;
`word_eq` compares words:

```python
a = Braid([1, 2, 1], n_strands=3)
c = Braid([2, 1, 2], n_strands=3)
a == c  # True: the same braid
a.word_eq(c)  # False: not the same word
```

To compare braids however they are written — another starting point, more
repeats, the strands numbered from the other side — see {doc}`comparing_braids`.

## Drawing

`plot()` draws a braid's diagram with matplotlib; a 3D view needs its
strands as curves:

```python
from braidpy.parametric_braid import ParametricBraid

plait.plot()
ParametricBraid(plait.to_parametric_strands()).plot()
```

{doc}`visualization` shows each view.

## An interactive tour

`make demo`, from a clone of the repository, runs a short tour in the
console: each step shows a line of code and runs it when you press Enter.

## Next

- [Braid Studio](braid_studio.md): any braid in 3D, in the browser.
- {doc}`making`: how to make a braid on a kumihimo disk, a lace machine or
  Ashley's stand.
- {doc}`reference`: every module and function.
