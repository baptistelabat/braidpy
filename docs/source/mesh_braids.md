# Braiding over a mesh

Braiding so far starts from motion: a machine's carriers, a word's slots, a
parametric curve. A different kind of braid starts from a *shape*: strands
laid over the faces of a mesh, following its edges, passing over and under
one another where the pattern says so. Any closed mesh then carries a braid —
a torus, a handle, a last, a lamp shade — and the braid covers it evenly
whatever the shape.

This page states that problem as braidpy would pose it: the inputs, the
methods, what each takes and returns and refuses, how the pieces compose, and
how to tell whether it worked. Nothing here is implemented in braidpy. It is
a specification, not a description — like [Solving a braid's shape
numerically](solving_numerically.md), which it complements: that page settles
strands held by tension in space; this one lays strands held by the surface
they lie on, where there is nothing to tighten and the crossings are decided
by counting, not by force.

---

## What kind of braid this is

A strand of a mesh braid walks from face to face across the mesh's edges. At
each edge it crosses a fixed number of other strands — the edge's *strip
count* — and at each face it turns or goes straight, passing over or under
the strands it meets. Nothing is pulled taut: the surface carries the shape,
and the weave carries the crossings. What braidpy gains is a braid over
*any* shape, and — because the result is ordinary strand curves in space —
the whole downstream of what exists already: drawing, comparing, describing,
and the MCP tools, unchanged.

It is worth being clear about what this is not. It is not `take_off`: no
fell, no take-off, no carrier motion, and no contact physics — a strip that
would overlap its neighbour is a miscount, not a force to push apart. The
specification's job is to make the counting right by construction.

## Provenance

The pipeline below follows the stages of florarobotica's PolyMeshLib.Braid
(a Visual Basic Grasshopper library, unlicensed and dormant since 2019,
read as ideas only — no code, no names and no data of it come across): solve
a strip count for every edge, equalise the paths' lengths, trace the strands,
look up a tile plan at each face, and build the geometry. Everything here is
re-derived from that reading against braidpy's own conventions; where the
two differ, this page is what braidpy would do.

## The mesh

    weave.Mesh(vertices, faces)

A new value type, in a new subpackage `braidpy.weave` (the same layout
`take_off` uses: small modules, one stage each).

- `vertices`: shape `(n, 3)`, the corners in space.
- `faces`: one loop of vertex indices per face; triangles and quads to
  start, any valence in principle.

Derived once, in `__post_init__`: the edges (unordered vertex pairs), the
faces each edge borders, and the adjacency both ways. The mesh must be
manifold enough to weave over: every edge borders one or two faces — one is
a boundary edge — and no face visits a vertex twice. Anything else raises
`ValueError`, naming the offending edge or face. Vertices may be shared by
any number of faces; vertex normals come from the average of its faces',
normalised.

Ordering is part of the value: faces and their loops are kept as given, and
every later stage breaks ties by index, so two runs over the same mesh give
the same braid.

## Stage 1: how many strips cross each edge

    weave.strip_counts(mesh, sources, smallest=1) -> dict[edge, int]

From the edges named in `sources`, breadth-first over the vertices: each
edge is given the count it must carry for the weave to pass through it, and
the wavefront carries the counts outward. The count is what makes the weave
close: round any vertex, the strips arriving must leave in pairs, so the
counts of the edges about a vertex must admit a pairing of their half-edges.
A vertex where they do not is reported by name and index in a `ValueError`,
with the counts found — the user's way in is to move `sources` or add
edges, and the error should say which vertex defeats them and why.

Args:

- `sources`: edges of the mesh the strands start from; a boundary's edges,
  for an open braid, or a spanning set for a closed one.
- `smallest`: no edge carries fewer strips than this. PolyMeshLib default 3;
  braidpy defaults to 1 and lets the caller ask for more.

Returns the count per edge. Every edge is covered or the mesh is not
connected from `sources`; an unreachable region is a `ValueError` too.

## Stage 2: how long each crossing is

    weave.face_counts(mesh, strip_counts) -> dict[edge, int]

Traced strands must meet the same number of faces between two visits to the
same place, or the tiles do not line up and the weave will not close. This
assigns a face count per edge — how many faces a strand crosses along it —
so that every walk the next stage traces has the same total. It is a longest
path problem over the vertices, solved as PolyMeshLib solves it: walk from
every source, take each vertex's depth as the longest walk reaching it, then
raise every sink to the longest walk of all. Edges left with an impossible
difference are a `ValueError`, naming the edge.

## Stage 3: the strands' walks

    weave.trace(mesh, strip_counts, face_counts) -> list[Walk]

Turns the counted mesh into strands: directed, edge-disjoint walks, each
edge crossed exactly its strip count times, each visit to a vertex leaving
by a different edge than it arrived by. A walk that returns to its start
closes; one that reaches a boundary edge ends there. Output is one `Walk`
per strand: the sequence of `(edge, face, direction)` it takes, in order.

The invariants that make this testable:

- every edge is used exactly `strip_counts[edge]` times, counted over all
  walks;
- no walk visits a vertex twice without closing in between;
- every walk is either closed or ends at a boundary.

A vertex where the pairing cannot be continued — every exit edge used up —
is a `ValueError` naming the vertex and the walk that is stuck. Tracing is
deterministic: exits are tried in the mesh's own index order.

## Stage 4: the tile a face weaves

    weave.tile_plan(face, strip_counts) -> list[Plan]

At each face, the strip counts of its edges, read in order, pick a *tile
plan*: where each strand enters and leaves, whether it turns, and whether it
passes over or under each strand it meets. The plans live in a dictionary
keyed by that configuration, default ones written for the shapes worth
having first — a triangle with one strip per edge, the quad cases, the
2-strip triangle — and a caller may put their own in. A configuration with
no plan raises `NotImplementedError` saying what the face's counts were: the
dictionary is meant to grow, case by case, and the error is the queue.

The over/under decision is where this differs from everything else in
braidpy: it is *chosen*, by the tile, not settled by physics. Which strand
goes over is what makes two weaves different braids, so the tile plan is
part of the specification of a weave, the way a word is for a braid.

## Stage 5: from tiles to strands in space

    weave.weave(mesh, sources, smallest=1, tiles=None) -> ParametricBraid

Composes the stages: strip counts, face counts, walks, tile plans, and then
geometry. Each tile plan places its strands' points inside its face — a
small grid per tile, as PolyMeshLib's tiles do — lifted off the surface
along the normal by a fraction of the strand's thickness, so strands do not
sit in the surface they cover. Each strand's points, face by face along its
walk, are joined and smoothed (a Catmull–Rom spline through the tile points;
the polyline stays available, as `take_off` keeps its samples). One strand
per walk, in the order traced, as a `ParametricBraid` — so drawing,
comparison and the MCP tools work on a mesh braid with nothing new.

Args:

- `smallest`: passed to `strip_counts`.
- `tiles`: extra tile plans, keyed as `tile_plan` keys them, over the
  defaults.
- Thickness comes with the mesh: a `strand_width` on `Mesh`, defaulting to
  a tenth of a typical edge, used only to lift the strands — there is no
  yarn to overlap here, and `tighten_yarns` is not called.

## How to know it worked

1. **The counts are respected.** After `trace`, every edge's crossings
   number exactly its strip count — a cheap, complete check over the walks.
2. **Walks close or end at a boundary**, and never revisit a vertex in
   between.
3. **Two runs are identical.** Every stage is deterministic by index order;
   a test weaves twice and compares strand for strand.
4. **Golden meshes.** A tetrahedron, a cube and a quadrilateral torus, each
   with known counts, give known walks and tiles; their rendered braids are
   the fixtures.
5. **The torus reads as a braid word.** A weave over a quad torus, cut
   along two loops, is an ordinary braid: its crossings, read tile by tile,
   give a word that `Braid` accepts and that matches the word of the same
   pattern laid by hand. This is the one check that ties the new kind of
   braid to everything braidpy already knows.

## Out of scope, on purpose

- No tension, no contact, no settling: the surface carries the shape. If a
  mesh braid is ever to sag or stretch, that is a solver of its own, on the
  pattern of [solving a braid's shape numerically](solving_numerically.md).
- No strip material, width per strand or colour ways beyond the drawing's.
- No re-meshing: the user's mesh is the truth, and its edges are the
  strands' paths. A bad mesh weaves badly, and says so.
