# Wood

## 1. Overview
Wood surfaces: coated (varnished) wood, cladding boards, battens and veneers. The look depends on
the coat and on how the grain is laid on the surface. Wear on wood edges is an effect covered in
edge-wear.md (plain-text neighbour), not here.

## 2. Layers and node-editor diagram
This file is a single material family, not a stack. The coat sits on the wood base in `coated_wood()`
(§4.1), and cladding grain is set by UV (§4.2). The coat rules in §4.3 and §4.4 apply to the same
coat, so there is no separate diagram.

## 3. Code
- `scripts/blender/materials/wood/wood.py`: `coated_wood()` (`materials.wood.wood`).
- `scripts/blender/core/archviz.py`: `archviz.directional_uv`, defined in `core/uv.py`.
- No control scene is named for this file.

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

### Generic layers, wood settings
| Layer | Reference | Wood note |
|---|---|---|
| Wear on wood edges | edge-wear.md (plain text) | covered there, not in this file |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Satin varnish built with a strong rough coat | coat trap: satin is a low weight with tight roughness | low coat weight, tight coat roughness (§4.1) |
| Wood base too glossy | IOR lowered to compensate for the coat | spread base roughness toward matte; leave IOR (§4.1) |
| Grain runs across the boards | plank map grain along V, not set | `along="V"` (§4.2) |
| Halos on battens and veneers | glossy coat mirrors lenses | matte coat (§4.3) |
| Dark veneer floor reads light grey at a low angle | satin coat; Fresnel reflects the sky | matte coat (§4.4) |

Generic problems that show up in any material are in troubleshooting.md.
