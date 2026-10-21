# Bridges between ways of braiding

braidpy makes a braid many ways: as a braid word, on a kumihimo disk, on
Ashley's stand, on a braiding machine, on a Jacquard lace machine. Each
already gives the braid it makes, as a braid word. A bridge goes the other
way: from a braid — a braid word, say — to how to make it another way.

Two braids are the same braid, for a bridge, when nothing braidpy measures
of their topology tells them apart ({func}`~braidpy.ring_program.same_braid`,
see {doc}`comparing_braids`): a way of making a braid need not make its very
word, only the same braid. Each bridge is checked by reading the braid back
off what it made, with the code that reads it off that way of making
braids, and comparing.

## Neighbours swapping places round a ring

A braid word, a kumihimo disk and a lace machine all make a braid by
moving strands round a ring of places, two neighbours at a time. A
{class}`~braidpy.ring_program.RingProgram` says so once, for all of them:

- the places round the ring, and which strand starts where — a place may be
  empty;
- rows of **swaps**: two neighbouring places exchanging what they hold, the
  swaps of a row sharing no place, so made at once. A swap's sign is the
  crossing's, as a braid word writes it: positive when the strand on the
  right is lifted over the one on its left. A swap with an empty place moves
  a strand on by a place and crosses nothing.

```python
from braidpy import Braid
from braidpy.ring_program import from_braid

plait = Braid((1, -2) * 3, 3)
program = from_braid(plait, n_places=6)   # three strands, three empty places
program.braid() == plait                  # True: read back off its disk moves
program.disk()                            # the same, as a disk's moves
```

A braid word becomes a ring program crossing by crossing
({func}`~braidpy.ring_program.from_braid`), the crossings packed into rows
where they commute. It is read back as a disk braid is
({func}`~braidpy.take_off.disk_annular_word`): a swap is the lifted strand
moved over its neighbour, then the neighbour into the place it left.

Moving strands round the ring is not free. The ring has a seam, between its
last place and its first, and strands carried across it twist the braid
below them, as carriers going round a tubular braiding machine do: every
strand once round the ring is a full twist. A program that moves strands to
other places through empty ones keeps them off the seam, or brings them
back.

## What comes next

Each way of making braids is a step of its own, built on the ring program:

1. **A kumihimo disk** (mobidai): each swap as moves through the disk's
   empty slots, made and read back by the disk's own code.
2. **The Jacquard lace machine** (`jacquard_lace_ring`): its notches are the
   ring's places, a gear's half turn the swap of the two carriers beside it,
   and a step of the punchcard the gears turned, one line per way of
   turning. A gear always turns the same way, so a crossing's sign is fixed
   by where it is made: strands are moved, through empty notches, to where
   their crossings can be made, and a braid that cannot be made on the
   machine is said to be so, and why. The card is checked by running the
   machine and reading its braid back.
3. **Ashley's stand** (the marudai of {doc}`braid_studio`'s sinnets): a move
   carries a strand across several spaces, so this bridge searches for a
   sinnet — its spaces, the strands in each, its moves — with the braid's
   topology.
4. **Braid Studio**: "Make it as…" beside the braid, each way's moves or
   punchcard to read, download, and make.
