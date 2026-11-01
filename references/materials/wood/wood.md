# Wood

## 1. Overview
Wood surfaces: coated (varnished) wood, cladding boards, battens and veneers. The look depends on
the coat, on how the grain is laid on the surface and on how its edges wear (§4.5).

## 2. Layers and node-editor diagram
This file is a single material family, not a stack. The coat sits on the wood base in `coated_wood()`
(§4.1), and cladding grain is set by UV (§4.2). The coat rules in §4.3 and §4.4 apply to the same
coat, so there is no separate diagram. Worn edges (§4.5) use the edge field and chips of
[edge-wear.md](../../effects/edge-wear.md).

## 3. Code
- `scripts/blender/materials/wood/wood.py`: `coated_wood()` (`materials.wood.wood`).
- `scripts/blender/core/archviz.py`: `archviz.directional_uv`, defined in `core/uv.py`.
- Worn edges: `round_geometry(obj)` (`effects/round_edges.py`), `wood_wear_group`
  (`wood_damage.py`), `weathered_wood` (`wood_shading.py`); control `scripts/controls/material/wood_wear_graph_check.py`.

## 4. Instructions and parameters, per layer

### 4.1 Coated wood (satin varnish)
- **The coat trap:** satin varnish is a *low* coat weight with *tight* coat roughness, not a strong
  rough coat.
- Spread the base roughness toward matte. Do not lower IOR to compensate.
- Coat › Normal can stay smooth over bumped wood (to try).

| Parameter | Value |
|---|---|
| Coat weight | low |
| Coat roughness | tight |
| Base roughness | spread toward matte |
| IOR | do not lower to compensate |
| Coat › Normal | can stay smooth over bumped wood |

### 4.2 Cladding grain (directional UV)
- Pick the plank map by its real size, then run `archviz.directional_uv(obj, tex_size_m, axis)` so the
  grain follows the boards.
- A map whose grain runs along V needs `along="V"`.

| Parameter | Value |
|---|---|
| Map size | the plank map's real size |
| Call | `archviz.directional_uv(obj, tex_size_m, axis)` |
| `along` | `"V"` when the grain runs along V |

### 4.3 Battens and veneers
- Battens and veneers want matte. A coat mirrors lenses as halos.

| Parameter | Value |
|---|---|
| Coat | matte |

### 4.4 Dark veneer floor at a low camera angle
- A dark veneer floor seen at a low angle reads light grey under a satin coat: Fresnel reflects the
  bright sky at grazing angles.
- A matte coat keeps it dark.

| Parameter | Value |
|---|---|
| Coat | matte |

### 4.5 Worn edges
- A real rounded edge (`round_geometry(obj)`), not a shaded one, then `wood_wear_group`: dents on the edges
  and breaks on up-facing faces, the break noise stretched along the grain so it reads as split timber.
- Shader (`weathered_wood`): worn edge = varnish off + grime; exposed wood lifted toward a raw tint.
- The break share responds steeply: a small fraction of the top reads as wear, a little more as damage.
  Bisect it against a render.

### Generic layers, wood settings
| Layer | Reference | Wood note |
|---|---|---|
| Edge field and chips | [edge-wear.md](../../effects/edge-wear.md) | wood uses its own group (§4.5) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Satin varnish built with a strong rough coat | coat trap: satin is a low weight with tight roughness | low coat weight, tight coat roughness (§4.1) |
| Wood base too glossy | IOR lowered to compensate for the coat | spread base roughness toward matte; leave IOR (§4.1) |
| Grain runs across the boards | plank map grain along V, not set | `along="V"` (§4.2) |
| Halos on battens and veneers | glossy coat mirrors lenses | matte coat (§4.3) |
| Dark veneer floor reads light grey at a low angle | satin coat; Fresnel reflects the sky | matte coat (§4.4) |
| Worn wood reads as damaged | break share too high | bisect the break share (§4.5) |

Generic problems that show up in any material are in troubleshooting.md.
