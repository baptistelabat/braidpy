# Changelog

What changed in each release of braidpy.

## 0.3.0 — unreleased

braidpy grows from braid words to the braids people make: on braiding and
lace machines, kumihimo disks, a marudai and Ashley's stand, laid and
settled in 3D, compared by their topology, and shown in Braid Studio, in the
browser.

### New

- **Braid Studio**, a web page where braidpy runs in the browser: describe a
  braid — a word, a kumihimo or mobidai pattern, an Ashley sinnet, a braiding
  or lace machine — and see it laid, tightened and made in 3D, with nothing
  installed. The braids it offers are made and settled with the site, and
  shown at once.
- **Braiding machines** (`braidpy.horn_gear`): horn gear (maypole) machines,
  flat, tubular and soutache, and the Jacquard lace machine driven by its
  punchcard; their tracks, collisions, threading and animation, and their
  handle turned by hand.
- **Kumihimo and mobidai disks**, animated from above, and **43 of Ashley's
  solid sinnets** (ABOK #2965–#3082), each worked on its stand, with its
  braid word and its mobidai pattern.
- **A braid made move by move on a marudai** (`braidpy.marudai`), each yarn
  carried over the others and drawn tight.
- **Ways of making a braid** (`braidpy.making`): from a braid word to how to make it — moves
  on a kumihimo disk, a Jacquard lace punchcard, a sinnet on Ashley's stand —
  each checked by reading the braid back off what it makes.
- **Comparing braids** (`braidpy.similarity`, `braidpy.topology_catalog`): a
  fingerprint that does not change however a braid is written, the braids
  most like one, and a catalogue of braids by topology with every way of
  making each.
- **The shape of a braid**: laid in 3D as it comes off whatever made it, and
  tightened; closed forms for the shapes that have one (a laid rope, a
  braided tube, the flat braid); yarns settled by their own physics
  (`braidpy.rope`, `braidpy.form`), in Python and in the page.
- **For AI assistants**: `braidpy.tools`, a few questions answered in plain
  data, and `braidpy-mcp`, an MCP server offering them (`pip install
  "braidpy[mcp]"`).
- Linking numbers, pure braids and their closures, full twists, the braid
  word read in any of its notations (`braidword.parse_word`).

### Changed

These may need changes to code using 0.2.2.

- **Drawing is an extra**: matplotlib, plotly and imageio are installed with
  `pip install "braidpy[viz]"`; `pyqt6` and `tornado` are no longer
  required. braidpy alone installs in 100 MB rather than 489 MB, and a
  drawing library missing says what to install.
- **Python 3.10 to 3.15** are supported, and tested daily.
- The 2D braid diagram is drawn by braidpy itself, in its own colours.
- `GarsideCanonicalFactors.n_half_twist` counts half twists (it counted full
  ones).
- Handle reduction (`braidpy.handles_reduction`) has a new interface.
- `Braid ==` and `is_trivial()` are decided by handle reduction, math-braid's
  normal form only when it is slow: faster on most braids.
- Drawing libraries, sympy and math-braid are imported only when used.

### Fixed

- Comparing a braid with the trivial braid crashed; `is_trivial()` looked
  only at the word, so `σ₁σ₁⁻¹` was not trivial.
- Parametric strands stopped short of their end.
- The documentation's 3D example passed a braid where an amplitude was
  expected (issue #8).

### Documentation

- In three parts: a user manual, a theory manual and a developer guide, with
  an API reference covering every module.

## 0.2.2

The release before these notes were kept: braids as words in Artin's
generators, their operations and properties, handle reduction, and their
drawing in the console, in 2D and in 3D.
