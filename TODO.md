# To do

What is known and left for later, each with enough said to pick it up.

## Before or around a release

- **Two Braid Studio braids are laid too coarsely to tighten reliably**:
  a two-strand word settled by physics (yarns move 3.7 diameters sideways
  between two levels) and a lace braid made on a marudai round a rigid core
  (3.0). Tightening warns of it (`take_off.SAFE_STEP`); lay them in more
  samples.

## Later

- **Reducible, periodic or pseudo-Anosov** (`Braid.is_reducible` is a stub).
  No library fits: `flipper` and `curver` (MIT) took over two minutes on
  three strands, and libbraiding is not on PyPI. Garside theory decides it,
  on the super summit sets `conjugacy` already computes:
  - Benardete, Gutiérrez and Nitecki, *A combinatorial approach to
    reducibility of mapping classes* (1993): a reducible braid has a
    conjugate in its super summit set that keeps a round curve, one round
    strands i to j. The place to start.
  - Lee and Lee, *A Garside-theoretic approach to the reducibility problem
    in braid groups*, J. Algebra (2008): the ultra summit set suffices.
  - González-Meneses and Wiest, *Reducible braids and Garside theory*,
    Algebr. Geom. Topol. 11 (2011): round or almost round curves in the
    sliding circuits set; libbraiding's way.
  - Calvez, *Fast Nielsen–Thurston classification of braids*, Algebr. Geom.
    Topol. 14 (2014): polynomial for a given number of strands.
  - Birman, Gebhardt and González-Meneses, *Conjugacy in Garside groups III:
    periodic braids*, J. Algebra (2007).
  - Bestvina and Handel, *Train-tracks for surface homeomorphisms*, Topology
    (1995): the other way, flipper's.

  Then Braid Studio's card can say which of the three a braid is.
- **Lace braids on the front page**: they have no topology, so their
  strands, loops and writhe are not shown. A lace machine's braid has a
  braid word: adding lace to the topology catalogue's methods would give
  them.
- **An axial that stays straight but moves**: a triaxial braid's axials are
  tensioned yarns, straight, yet free to shift sideways as the braid closes
  up. A core is either of yarn (bends) or rigid (does not move at all).
- **Docstrings of private helpers**: coverage is 88%; what lacks one is
  mostly `conjugacy`'s internals and `web.disks`' builders.
- **One spelling**: `*_catalog` modules beside `catalogue.py`. Renaming
  breaks imports.
