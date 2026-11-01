# Edge wear: edge line, edge dust, chips, run-off and cracks

## 1. Overview
Weathering that follows the shape of an object; Blender has no edge-wear node, so this is a recipe. Edges are
slightly rounded; every edge, outside or inside, gets a thin dark line and a wider, lighter dust; outside
edges chip; walls get run-off below their drip edge and cracks from openings and edges.

Every size is a dial, not a value: a chip is millimetres on a close-up and centimetres across a courtyard.
Set it from the pixels it covers in the shot and judge the first render (RULES MAT_03).

**Use when:** an edge or corner needs dirt, dust or chips, or a wall needs run-off or cracks. Per-unit
variation and grunge strength: variation.md.

## 2. Layers and node-editor diagram
```
 ┌─ EDGE WEAR ───────────────────────────────────────────────────────┐
 │ 4.1 Rounded edge  → normal (shader Bevel) or real bevel geometry   │
 │ 4.2 Edge field    → distance to outside edges and inside corners   │
 │ 4.3 Edge line     → albedo, roughness: thin, dark, at the edge     │
 │ 4.4 Edge dust     → albedo: lighter, wider, fading onto the faces  │
 │ 4.5 Chips         → mesh along −normal + fresh-break colour        │
 │ 4.6 Run-off       → albedo on vertical faces below a drip edge     │
 │ 4.7 Cracks        → albedo, groove from openings and edges         │
 └───────────────────────────────────────────────────────────────────┘
 leak field (4.6) ─► edge field (4.2) ─► chips (4.5) ─► shading masks (4.3, 4.4, 4.6, 4.7)
```
- The leak field runs first, on the clean mesh; any raycast or proximity field runs before modifiers that
  move the mesh (§4.6).
- Chips are geometry; every other layer is a shading mask, multiplied in. Each layer has its own switch, an
  `amount` (0 = off) or flag, default on (RULES MAT_07); strengths are set per scene.

## 3. Code
`scripts/blender/effects/`, imported through `effects.edge_wear`:
- `round_edges.py`: `set_round_radius`, `round_shader`, `round_geometry`, `switch_rounding` (§4.1).
- `edge_chips.py`: `dice`, `edge_wear_group`, `add_edge_wear`, `set_input` (§4.2, §4.5);
  `edge_masks.py`: `mask_material`, edge masks side by side (§4.2).
- `edge_dirt.py`: `edge_dirt_masks`, `add_corner_dirt` (§4.3, §4.4); `edge_shading.py`: `weathered_concrete`.
- `leak_field.py`: `add_leak_field`; `runoff.py`: `add_runoff` (§4.6).
- `cracks.py`: `add_cracks(mat, openings)`; `edge_cracks.py`: `add_edge_cracks`; crooked paths in
  `crack_ribbon.py` (§4.7).
- LuxCore inside corners: `scripts/blender/renderer/luxcore/dust_shader.py`, `bake_dust` (§4.2).
- Controls (`scripts/controls/effects/`): `edge_wear_lab.py` (every layer on/off), `edge_dirt_lab.py` (line and
  dust), `edge_wear_graph_check.py` (graph baseline), `weathering_lab.py` (run-off on a flat wall).

## 4. Instructions and parameters, per layer
### 4.1 Rounded edge
- No real edge is sharp: a slight rounding catches the light and keeps the edge itself clean (the line sits
  just behind it, §4.3). One radius for the scene (default ~2–3 mm), set from the shot; materials carry none.
- Shader Bevel by default. Real bevel geometry for close-ups, a visible silhouette, chips, or MNEE caustic
  casters and receivers, where the shader Bevel is invalid.

### 4.2 Edge field
- Outside edges: GN Edge Angle (convex over a threshold) → Proximity → `edge_dist` in metres, plus
  `rest_pos`. Exact, clean, cheap; Pointiness, AO Inside and a Bevel-normal mask lost on the test.
- Inside corners: AO with Inside off and Only Local off, so a floor and a wall that are separate objects
  still meet. Cap it so a corner where three faces meet is no darker than a two-face joint. LuxCore has
  no AO texture: bake it per object (`bake_dust`, 4096 px). Bake for repeated renders.
- An object without the GN modifier reads `edge_dist` 0, "on an edge", and goes uniformly dirty: add a large
  offset where `length(rest_pos) < epsilon` before the band remap.

### 4.3 Edge line
- One continuous line that varies, never dashes or an outline: long runs (metres), rare short gaps, near-constant
  width (±~15 %), the variation in darkness; fine speckle inside the band only (RULES MAT_05).
- Peaks a few mm behind the edge, which stays light (§4.1). Strongest where an underside meets the edge (water
  wraps back), about half on up-facing edges, and it runs through every corner where edges meet.
- Inside corners carry almost no line, mostly dust. Clean where a chip removed material (× (1 − chip)).
- Set its strength from a reference: match the band-to-face brightness ratio and the dirty share of the edge.

### 4.4 Edge dust
- Lighter than the line, several times wider, fading smoothly onto every face it touches. Tonal order:
  surface > dust > line. Both darken the surface's own colour and keep its texture; a fixed colour reads as a
  pale highlight or a black stroke. Inside corners: strongest low down, fainter at the ceiling (RULES MAT_06).
  Judge the width on the full frame.

| Parameter | Starting value |
|---|---|
| Line width | ~20 mm |
| Dust width | ~150 mm |
| Line / dust | surface albedo × ~0.5 / × ~0.8, slightly greyer |

### 4.5 Chips and fresh break
- `dice(obj)` first (Rhino meshes are too coarse), then `add_edge_wear(obj, edge_wear_group(), …)`.
- Size in order, each from the one before: chip reach (from the shot) → band (contains the reach) →
  subdivision (a chip spans several faces).
- Only on objects with outside edges in view; floors and slabs stay coarse. At room scale use about half the
  close-up chip size and a lower chipped share. Repeated objects: `Seed=(x, y, z)` per object.
- Mesh already dense from another modifier: the same chip field in the material displacement (noise on a
  stored rest position). Risk: adaptive displacement can run out of VRAM on a small GPU.
- Fresh break: a chip exposes the inner material, the same material but never weathered. Take its colour
  from the clean base, before grime layers, made lighter and rougher, with a fine fracture bump. Taken from
  the finished colour, a chip reads as a dark spot.

| Parameter | Value |
|---|---|
| Chip reach / depth | from the shot (defaults 45 mm / 18 mm) |
| Chipped share | ~0.55 close-up, lower at room scale |
| Fresh break | clean base × ~1.15, roughness ~0.95 |

### 4.6 Run-off
- Streaks start where water leaves a surface. With eaves, sills or rakes above: `add_leak_field` raycasts up
  to the drip edge (`leak_d`), then `add_runoff`. A wall whose top is the drip edge: build from its stored
  top and foot instead.
- Gravity-shaped: streaks stretched down (~×14 across, ×0.6 down), each its own length (~1–3 m), clustered
  and patchy along the wall; vertical faces only. Isotropic noise alone reads as smoke.
- On a sunlit wall streaks need full strength to read.
- Design it on the flat test wall first (`weathering_lab.py`), then install the same graph; check it adds no
  step at joints.

### 4.7 Cracks
- Never straight: a jagged path that kinks at irregular steps, with fine wobble, short branches and a width
  that tapers and varies.
- Opening cracks: from re-entrant corners, heading 45° (±15) out of the opening, 0.4–1 m. Edge cracks: short
  (~5–20 cm), sparse, heading roughly square into the face from an outside edge.
- A hairline is invisible at room scale; what reads is a dirt-darkened crack (core ~5 mm, halo ~20 mm) on a
  shallow groove. Keep a few, never a symmetric set: an opposite pair reads as one line.

### Generic layers
| Layer | Reference | Note |
|---|---|---|
| Per-unit variation, grunge | variation.md | weathering here is gravity-shaped |
| Faint edge on huge meshes | `references/materials/concrete/concrete.md` | Bevel-normal mask instead of dicing |
| Worn wood edges | `references/materials/wood/wood.md` | real bevel and grain-wise breaks |
| Cracks in glazed tiles | [tiles.md](../materials/tile/tiles.md) | per-tile Voronoi network |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Whole floor uniformly dirty | `edge_dist` reads 0 without the modifier | gate on `rest_pos` (§4.2) |
| Floor/wall joint gets no dirt | AO with Only Local on | Only Local off (§4.2) |
| Black blob where three faces meet | AO pools the line | cap the corner field (§4.2) |
| Dust reads as a pencil line from afar | width judged up close | judge on the full frame (§4.4) |
| Chips look chewed on a far beam | close-up sizes at room scale | halve size, lower share (§4.5) |
| Identical chips on repeated objects | same noise lookups | seed per object (§4.5) |
| Dark spot at each chip | fresh break from the grimed colour | fresh break from the clean base (§4.5) |
| Light triangles hanging from an edge | leak field after the chips | leak field first (§4.6) |
| Weathering reads as smoke | isotropic noise | gravity-shaped streaks (§4.6) |
| Two cracks read as one line | opposite pair | a few, not symmetric (§4.7) |
| Cracks look drawn | straight paths | kinked, wobbling, branching path (§4.7) |

Generic problems: troubleshooting.md.
