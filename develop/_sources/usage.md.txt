# 🛠️ Usage Guide

(Installation)=
## Installation

To use **braidpy**, first clone the repository:

```bash
git clone git@github.com:baptistelabat/braidpy.git
```

Then install the required dependencies:

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation).
2. Or simply run:

   ```bash
   cd braidpy
   make install-uv
   ```

---

## 🚀 Launching the demo *(In Progress)*

If you have `make` installed, you can launch the demo using:

```bash
make demo
```

---

## 🔁 Creating braids (Artin Generators)

To create a braid, you need to define operations called **Artin generators**, representing crossings of two strands.

Imagine a 3-strand braid:

- Strand 1: Left
- Strand 2: Middle
- Strand 3: Right

### ➕ Positive crossing (Above)

Move strand 1 **over** strand 2:

```python
first_upcrossing = Braid([+1], n_strands=3)
```

### ➖ Negative crossing (Below)

Move strand 1 **under** strand 2:

```python
first_downcrossing = Braid([-1], n_strands=3)
```

This is the inverse of the first:

```python
first_downcrossing = first_upcrossing.inverse()
```
The inverse can be seen as the image of the braid in a mirror. We will see that this holds for any braid.

### 🖼️ Visualizing

```python
first_crossing.draw()
```

This shows strand 1 going over strand 2. Intermediate steps are shown with an arrow from the braid moving abobe the other one:

```
1 2 3
1>2 3
2 1 3
```

---

## 🔄 Next crossing

Move the new middle strand (strand 2) below strand 3:

```python
second_crossing = Braid([-2], n_strands=3)
```

---

## 🔗 Combining braid operatin

Using a list:

```python
b = Braid([1, -2], n_strands=3)
```

Or by multiplying:

```python
basic_step = first_upcrossing * second_crossing
```

The resulting braid is:

```
1 2 3
1>2 3
2 1<3
2 3 1
```

---

## 🔁 Creating a Pure Braid

As you may, with this typical braid, if we reepeat the `basic_step` three times we return to original order of strands:

```python
braid = basic_step * basic_step * basic_step
```

Or simply:

```python
braid = basic_step ** 3
braid.draw()
```

Visual:

```
1 2 3
1>2 3
2 1<3
2>3 1
3 2<1
3>1 2
1 3<2
1 2 3
```

This is called a pure braid. A **pure braid** restores the original strand order.

You can check this with:
```python
braid.is_pure()
```

---

## ✂️ Handle Reduction

Now consider applying handle reduction on a series of braids:

```python
for n in range(2):
    b1 = Braid([+n+1], n_strands=3)
    b2 = Braid([-n], n_strands=3)
```
