# To do

What is known and left for later, each with enough said to pick it up.

## Before or around a release

- **Two Braid Studio braids are laid too coarsely to tighten reliably**:
  a two-strand word settled by physics (yarns move 3.7 diameters sideways
  between two levels) and a lace braid made on a marudai round a rigid core
  (3.0). Tightening warns of it (`take_off.SAFE_STEP`); lay them in more
  samples.

## Later

- **Ashley's method, from a shape**: what the book does that it does not.
  - The order of the moves of a square or an oblong on a corner (#3070,
    #3073 to #3075): the shape draws the book's lines, the book makes the
    moves in an order of its own, moving opposite strands together.
  - Pentagons and pentalphas (#3079 to #3082): on no grid; a grid of
    lines at fifths of a half turn would hold them.
  - A hollow shape's braid is made round the hole, inner and outer spaces
    in turn, but has not been checked to tighten into a tube.
  - Braid Studio's *Find a sinnet* still searches blindly
    (`making.ashley.ashley_sinnet`, three seconds): a braid that a shape
    makes could be offered its shape instead.

- **Which of the three a braid is, said on Braid Studio's card**: it can
  now be told — `Braid.is_reducible` asks the super summit sets
  `conjugacy` computes, after Benardete, Gutiérrez and Nitecki 1993 and
  Calvez 2014, and `Braid.is_periodic` asks whether the nth or (n − 1)st
  power is a power of Δ.  What is left:
  - the answer needs the whole super summit set, exponential at worst;
    Lee and Lee's ultra summit set (J. Algebra 2008) or González-Meneses
    and Wiest's sliding circuits (Algebr. Geom. Topol. 11, 2011),
    libbraiding's way, would take fewer;
  - reducible says a round curve is kept, not which one: finding the
    reducing curves would let the card show the tubes;
  - Bestvina and Handel's train-tracks (Topology, 1995), flipper's way,
    remain the other road, slow in Python so far.
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
