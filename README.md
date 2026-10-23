# BraidPy

A Python library for working with braids, from braid theory to the braids
people make: by hand on a kumihimo disk, a marudai or Ashley's stand, or on a
braiding or lace machine. It aims to help design real 3D braids using recent
advances in braid theory, and to say how to make them.

- **[Braid Studio](https://baptistelabat.github.io/braidpy/studio/)**: braidpy
  in your browser. Describe a braid and see it laid, tightened and made in 3D,
  with nothing to install.
- **[Documentation](https://baptistelabat.github.io/braidpy)**: guides, the
  mathematics, and the API reference.
- **Sources** on [GitHub](https://github.com/baptistelabat/braidpy).

braidpy is in **alpha**: its features work and are tested, but its API may
still change between versions. What changed in each is in the
[changelog](https://github.com/baptistelabat/braidpy/blob/develop/CHANGELOG.md).

## Support

braidpy is built with [Claude Code](https://claude.com/claude-code). If it
helps you, you can [sponsor it](https://github.com/sponsors/baptistelabat):
sponsoring helps pay for that.

## Features

Braids in theory:

- [x] Braids as braid words in Artin's generators, read and written in the
      common notations (`σ₁σ₂⁻¹`, `1 -2`, `aB`, …)
- [x] Operations: product, inverse, powers, handle reduction, normal forms
- [x] Properties and invariants: permutation, purity, closure, linking
      numbers, Alexander polynomial, conjugacy
- [x] Whether two braids are the same braid however written, and the braids
      most like one, by a topological fingerprint
- [x] Drawn in the console, in 2D and in 3D
- [x] Annulus braids: crossings on a ring of slots, the wrapping crossing,
      turns

Braids people make:

- [x] Horn gear (maypole) braiding machines: flat, tubular, soutache and
      Jacquard lace, with tracks, collisions, threading and animation
- [x] Kumihimo and mobidai disks, animated from above, strands as spokes to
      the middle of the disk
- [x] Ashley's solid sinnets (ABOK #2965–#3082, 43 of them), worked on his
      stand, animated with the braid growing below
- [x] A braid made move by move on a marudai, each yarn carried over the
      others and drawn tight
- [x] Bridges: from a braid word to how to make it on a kumihimo disk, on a
      Jacquard lace machine's punchcard, or on Ashley's stand, each checked by
      reading the braid back off what it makes

The shape a braid takes:

- [x] A braid as it comes off whatever made it, in 3D: laid with no tension,
      converging on a fell ring about the braid's size, and tightened
- [x] Closed-form geometry for the shapes that admit one (a laid rope, a
      braided tube, the figure-eight flat braid), their clearances measured
      rather than assumed
- [x] From a 3D braid back to its braid word, for flat braids, so a computed
      shape can be checked against the braid it claims to be

Using it:

- [x] Braid Studio: all of the above on a web page, braidpy running in the
      browser
- [x] For AI assistants: a short front door (`braidpy.tools`) and an MCP
      server

Not yet:

- [ ] From a real, material braid to its 3D shape
- [ ] Finger loop braids (Kute-Uchi), a technique used and improved by nuns
      for centuries
- [ ] Track plans
- [ ] 3D rotary (hexagonal) braiding machines

## Basic example

```python
from braidpy import Braid

# Create a braid using list of Artin's generator
b = Braid([1, 2, -1])

# Display the corresponding braid word. You should get the notation as used by Artin 'σ₁σ₂σ₁⁻¹'.
b.format()

# Display using other common notation. You should get 'abA'.
b.format_to_notation(target='alpha')

# Draw the braid in console. Alternatively use result.plot() for more advanced 2D plot.
b.draw()

# Perform operations. See documentation for much more features !
result = b * b.inverse()

# Draw the resulting braid in console.
result.draw()

# Plot the resulting braid.
result.plot()

# Convert to parametric braid before ploting in 3D.
strands = result.to_parametric_strands()
from braidpy.parametric_braid import (
    ParametricBraid,
)
p = ParametricBraid(strands)  # .plot()
p.plot()
```

`result.plot()` gives the 2D diagram below — the braid runs down the page with its
word above it, each strand in the same colour the console draws it in, and the strand
passing behind interrupted where the two meet. `p.plot()` opens the 3D view.

![Plot braid example](https://raw.githubusercontent.com/baptistelabat/braidpy/develop/braid_plot.png)

## Braiding machines

A horn gear (maypole) braiding machine can be described, run and drawn. Half
its carriers travel one way round the ring of gears and half the other, and the
closed paths they run on decide which carriers can ever meet — which is what
decides the braid.

```python
from braidpy.horn_gear.examples import tubular_braid_8
from braidpy.horn_gear.tracks import compute_tracks, simulation_period
from braidpy.horn_gear.loading import load_carriers
from braidpy.horn_gear.simulation import simulate

machine = tubular_braid_8()
len(compute_tracks(machine))      # 4 closed tracks
simulation_period(machine)        # 8 steps to come home

history = simulate(machine, simulation_period(machine), load_carriers(machine))
```

Threading is a search, not a convention: `load_carriers` tries placements,
runs each one, and keeps the fullest that never collides. `visualize_machine`
and `animate` draw the result, and `scripts/gen_demos.py` writes a page per machine —
flat, tubular, soutache, diamond, and a Jacquard lace machine whose gears
interpenetrate and whose switches are driven by a punched programme.

## Braid Studio, in the browser

[Braid Studio](https://baptistelabat.github.io/braidpy/studio/) is braidpy on
a web page. Describe a braid as a braid word, a kumihimo pattern, a disk
braid, an Ashley sinnet or a braiding machine, and it is laid and tightened in
3D. braidpy itself runs in your browser through Pyodide, and three.js draws
the result. See [how to use it](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/braid_studio.md),
or run it locally:

```sh
make studio && make studio-serve   # then open http://localhost:8000
```

## Ashley solid sinnets

The solid sinnets of the Ashley Book of Knots are worked on a disk: each move
takes the earliest strand of a space over every strand it passes to another
space.

```python
from braidpy.solid_sinnets_catalog import abok_3042

abok_3042.braid()        # the braid word one cycle makes
abok_3042.to_mobidai()   # the same, as a kumihimo disk pattern
abok_3042.animate(n_cycles=3, side_view=True, output_html="3042.html")
```

## The shape a braid takes

Pulled tight, some braids have a shape you can write down. A laid rope does; so
does a braided tube; so does the classic flat braid. Most do not, and the
reason is not want of effort.

```python
import math
from braidpy.annulus_braid import lay_radius, packing_radius, tubular_braid_radius

packing_radius(3, 0.4)                          # 0.231 — the zero-lay limit
lay_radius(3, 0.4, lay=2.0)                     # 0.259 — where it really settles
tubular_braid_radius(8, 0.4, math.radians(45))  # 0.825 — in closed form
```

The documentation works each of these through, with figures generated from the
same functions:

- [The shape of a laid rope](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/laid_rope.md)
- [The shape of a braided tube](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/braided_tube.md)
- [Why a braid's shape has no closed form](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/why_no_closed_form.md)
- [Solving a braid's shape numerically](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/solving_numerically.md)

## Is it the same braid, and how is it made?

The same braid can be written many ways, and made many ways. braidpy
compares braids by their topology, and says how to make one by hand or on a
machine:

```python
from braidpy import tools

tools.compare_braids("1 -2", "-2 1")  # {'same_braid': True, 'distance': 0.0}
ways = tools.ways_to_make("1 -2")     # a kumihimo disk's moves, a lace punchcard,
ways["disk"]["moves"]                 # a sinnet on Ashley's stand
```

[Comparing braids](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/comparing_braids.md)
and [Bridges between ways of braiding](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/bridges.md)
explain how.

## For AI assistants

`braidpy.tools` answers the common questions in plain data, and
`braidpy-mcp` offers it to an assistant such as Claude as an MCP server:

```sh
pip install "braidpy[mcp]"
claude mcp add braidpy -- braidpy-mcp
```

See [braidpy for AI assistants](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/ai_assistants.md).

## 🛠️ Installation
Releases are on PyPI:

```bash
pip install braidpy        # or: uv add braidpy, poetry add braidpy
pip install "braidpy[viz]" # with what it draws with: matplotlib, plotly
```

braidpy alone computes everything; drawing braids (diagrams, 3D plots,
animations) needs the `viz` extra.

The development version, with what is not released yet, installs from
GitHub:

```bash
pip install "braidpy[viz] @ git+https://github.com/baptistelabat/braidpy@develop"
```

braidpy needs Python 3.10 or later; it is tested daily on 3.10 to 3.15.

## 🛠️ Installation from source
To work on braidpy itself, clone it (you are then on the `develop` branch)
and install it with [uv](https://docs.astral.sh/uv/), the project's package
manager. On Linux, from the root of the repository:

```bash
git clone git@github.com:baptistelabat/braidpy.git
cd braidpy
sudo apt-get install build-essential
make install-uv
```

---

## Test
The quick tests, in parallel, as every push runs them (a couple of minutes):

```bash
make test
```

Every test, the slow ones too, as CI runs them daily: `make test-all`. Only
the tests touching what you changed: `make test-changed`.

---

## 📜 Documentation
The documentation of the development version is on
[GitHub Pages](https://baptistelabat.github.io/braidpy), with Braid Studio
beside it; that of released versions is on
[Read the Docs](https://braidpy.readthedocs.io/en/latest/). To build it for
the version you have from source:

```bash
make docs
```

### Project Team:
This is a single person project for now, but I would be happy to make the team grow.

Human: 
- **Baptiste Labat**
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?logo=linkedin&logoWidth=20&style=flat-square)](https://www.linkedin.com/in/baptiste-labat-01751138/)
[![GitHub](https://img.shields.io/badge/-GitHub-black?logo=github&logoWidth=20&style=flat-square)](https://github.com/baptistelabat)

Bots:
- Claude Code
- chatgpt
- windsurf
---

## 🤝 Contributions

Contributions are welcome! Please open an [issue](https://github.com/baptistelabat/braidpy/issues) or submit a pull request from your fork to suggest changes, report/correct bugs, or propose new features.

The [developer guide](https://github.com/baptistelabat/braidpy/blob/develop/docs/source/developer_guide.md)
says how to set up, the rules braidpy is written by, how to test it and how
it is released. In short: English code and comments, Google-style
docstrings, type hints, and `pre-commit install` to check each commit.

## 📜 License
![License](https://img.shields.io/badge/license-MPL%202.0-brightgreen)

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](https://github.com/baptistelabat/braidpy/blob/HEAD/LICENSE) file for details.

---