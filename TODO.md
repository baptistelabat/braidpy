# To do

What is known and left for later, each with enough said to pick it up.

## Before or around a release

- **Leftovers to remove, or not** (each is public API, so removing it breaks
  imports; decided against for now):
  - `braid_catalog.triangle_sinnet_9` and `triangle_sinnet_10`: empty
    functions, and a loose note on a 14-strand D-shaped sinnet beside them.
    Make them, or move their links (craftdesignonline, loopbraider) to the
    references page.
  - `operations.py`: one function, `conjugate(b, c) = c·b·c⁻¹`, used only by
    a test, beside `conjugacy`.
  - `material_braid.py`: an early sketch, used only by its test; yarns with
    a thickness live in `take_off` and `rope` now.
  - `src/braidpy/analytic/`: no code, only a pointer to the documentation.
- **`flat_word` misreads a folded line of gears** (the three-band machine).
  It sorts the carriers left to right with one bubble pass a sample, a
  crossing per swap; where a line folds round, many carriers stand at
  nearly the same x and several swaps fall in one sample, and some are
  missed or recorded out of order. Read the same machine straight and
  folded, which cannot change its braid, and the traces of the powers of
  their reduced Burau matrices differ, though every pair of carriers winds
  round each other alike: a different braid, not another word of the same
  one. So the three-band machine's word, crossings, exponent sum and
  permutation in Braid Studio are not its braid's. Fix: sort each sample
  fully, ordering the swaps by when they happen, or read the word by angle
  round the deck as `annular_word` does; test it against the straight line,
  by the Burau traces.
- **Two Braid Studio braids are laid too coarsely to tighten reliably**:
  a two-strand word settled by physics (yarns move 3.7 diameters sideways
  between two levels) and a lace braid made on a marudai round a rigid core
  (3.0). Tightening warns of it (`take_off.SAFE_STEP`); lay them in more
  samples.

## Later

- **Split `take_off.py`** (1734 lines): trajectories for every source,
  laying, tightening, the checks (`least_take_off`, `longest_step`,
  `closest_approach`) and drawing, into a package, every name still
  importable from `braidpy.take_off`. A refactor: the same JSON for every
  Braid Studio build before and after.
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
- **Links for a braid on the website**: videos, drawings, the book. Each
  catalogue entry's `reference` (`catalogue.Entry`) is one string today,
  given only by Ashley's sinnets and the mobidai catalogue, and never shown.
  Make it a list of links, each a title, a URL and a kind (video, drawing,
  book, article), kept in the catalogues as data; export them with
  `web.catalogue()`, and list them on the braid's card. The topology
  catalogue can gather those of every way of making the same braid.
- **An axial that stays straight but moves**: a triaxial braid's axials are
  tensioned yarns, straight, yet free to shift sideways as the braid closes
  up. A core is either of yarn (bends) or rigid (does not move at all).
- **Docstrings of private helpers**: coverage is 88%; what lacks one is
  mostly `conjugacy`'s internals and `web.disks`' builders.
- **One spelling**: `*_catalog` modules beside `catalogue.py`. Renaming
  breaks imports.
