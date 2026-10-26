# Stone

## 1. Overview
Stone surfaces: long-strip pavers, polished speckled granite, large stone tiles, slab floors and
honed limestone or marble. Each look is its own material, chosen by the stone's finish and how it is
laid. The glazed, layout-driven tile system is a different case (tiles.md, plain-text neighbour).

**Use when:** stone pavers, slabs, polished granite or large-format stone tiles. Glazed tile with a
computed layout, cracks and relief: tiles.md (plain text).

## 2. Layers and node-editor diagram
This file has no stack. Each entry (§4.1 to §4.5) is one material with its own set of inputs, and
the entries are not combined. The one shared layer is per-unit variation on slab floors, a generic
layer in its own reference (§4.6), so there is no single diagram.

## 3. Code
- `scripts/blender/materials/stone/`: `stone.py` is the import point (`materials.stone.stone`).
  Entry points: `long_pavers` (`pavers.py`), `polished_granite` (`granite.py`), `stone_tiles`
  (`stone_tiles.py`).
- Slab floors (§4.4) have no code of their own: each slab or band is an object.
- Control: `scripts/controls/material/stone_graph_check.py` (deterministic graph and geometry
  baseline).

## 4. Instructions and parameters, per layer

### 4.1 Long-strip pavers
- A Brick Texture on (y, x) puts the long axis across the façade. Read the direction from which
  vanishing point the long joints run to.
- **Mortar has to stay legible at frame scale.** Too thin, or too close in tone, and the joints
  vanish entirely. Give it real width and a clearly darker grey, then set per-paver tone with
  Color1 and Color2.
- Call: `materials.stone.stone.long_pavers(tex_id, name, target, long_axis="Y")`.

| Parameter | Value |
|---|---|
| Long axis | `long_axis="Y"` in the call; direction from the vanishing point |
| Mortar | real width, clearly darker grey |
| Per-paver tone | Color1 and Color2 |

### 4.2 Polished speckled granite
- `materials.stone.stone.polished_granite()`: world-space Voronoi crystals sized to the real grain;
  the cell value drives a CONSTANT ramp of 3–4 stone tints. Low roughness, IOR 1.55, no coat.
- Edges by a Bevel modifier.
- Polished dark granite measures far darker than intuition suggests. Take the albedo off a
  reference, not from memory.

| Parameter | Value |
|---|---|
| Tints | 3–4, on a CONSTANT ramp |
| IOR | 1.55 |
| Roughness | low |
| Coat | none |
| Edges | Bevel modifier |

### 4.3 Large stone tiles
- `materials.stone.stone.stone_tiles()`: Brick Texture with offset 0 on BoxUV, per-tile tone, cloud
  noise plus specks, and recessed joints (`bump.invert = True`).
- Floors are glossier than walls and carry a coat.

| Parameter | Value |
|---|---|
| UV | BoxUV; Brick Texture offset 0 |
| Joints | recessed (`bump.invert = True`) |
| Floor finish | glossier than walls, with a coat |

### 4.4 Slab floors as separate pieces
- Model each slab or band as its own object. Per-object random variation (RULES MAT_06) makes
  neighbours differ, as laid stone does. Ranges are in the generic table (§4.6).
- Joints are a material hairline, slightly darker, not a gap.

| Parameter | Value |
|---|---|
| Unit | one object per slab or band |
| Joint | hairline, ≤ 1 mm, slightly darker |

### 4.5 Honed stone (lobby limestone and marble)
- Honed stone shows soft, blurred reflections of walls and people. Use Cycles roughness of about
  0.3–0.5, modulated by the map.
- A roughness exported from another renderer (for example 0.9) is not a Cycles value. Set it against
  the reference.

| Parameter | Value |
|---|---|
| Roughness | ~0.3–0.5, modulated by the map |

### 4.6 Generic layers, stone settings
| Layer | Reference | Stone note |
|---|---|---|
| Per-unit variation | [variation.md](../../effects/variation.md) | per-object random variation on slab floors (§4.4) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Mortar invisible at frame scale | joints too thin, or too close in tone | give real width and a clearly darker grey (§4.1) |
| Granite reads too light | albedo set from memory | take the albedo off a reference (§4.2) |
| Joints read as gaps | joint built as a gap | hairline joint, ≤ 1 mm, slightly darker (§4.4) |
| Neighbouring slabs look identical | one material for every slab | model slabs as separate pieces with per-object variation (§4.4) |
| Honed stone roughness 0.9 | another renderer's value used as is | set it against the reference, ~0.3–0.5 (§4.5) |

Generic problems that show up in any material are in troubleshooting.md.
