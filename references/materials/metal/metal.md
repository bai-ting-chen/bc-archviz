# Metal

## 1. Overview
Two metal looks. **Polished steel** is a metallic base with low roughness and smooth shading. **Brushed
anodised metal around water** adds brush anisotropy, bevels, water marks on tops and verticals, dust in
the joints and a little per-part tone, sized for the final view (RULES MAT_03). The water and grime
marks are described in this file itself.

## 2. Layers and node-editor diagram
Specific layers are described in §4. No generic layers apply to this file.

```
                                  METAL
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                             │
 │ 1 Polished base          → metallic BSDF (F82), roughness                 │
 │ 2 Brushed streaks        → anisotropy, roughness                          │
 │ 3 Edge bevel             → geometry, hardened normals                     │
 │ 4 Water marks            → colour, roughness                              │
 │ 5 Joint dust and tone    → colour (AO), per-part tone                     │
 └───────────────────────────────────────────────────────────────────────────┘
   tangent along the part's length (2) ─► anisotropy
   brush noise (2) ─► roughness
   bevel (3) ─► hardened normals ─► Principled Normal
   base (1) × per-part tone (5) ─► Base Color (edge tint brighter, warmer)
   water marks (4) + joint dust (5) ─► colour multipliers ─► Base Color
```

- The edge tint of the metallic BSDF is brighter and warmer than the base colour (§4.1).

## 3. Code
- `scripts/blender/materials/metal/metal.py`: `polished_steel(...)` (module `materials.metal.metal`).
- Brushed, bevel and water-mark layers: no script is named in this file.
- Control: none named in this file.

## 4. Instructions and parameters, per layer

### 4.1 Polished base
- `materials.metal.metal.polished_steel()`: Metallic BSDF F82, low roughness, shade smooth.
- Edge tint brighter and warmer than the base.

| Parameter | Value |
|---|---|
| BSDF | Metallic, F82 |
| Roughness | low |
| Shading | smooth |
| Edge tint | brighter, warmer than the base |

### 4.2 Brushed anisotropy
- Anisotropic, with the tangent from a directional UV along the part's length.
- Brush streaks in roughness: noise stretched ~400:1.

| Parameter | Value |
|---|---|
| Anisotropy | ~0.75 |
| Tangent | directional UV along the part's length |
| Brush streak stretch | ~400:1 |

### 4.3 Edge bevel
- Bevel with hardened normals.

| Parameter | Value |
|---|---|
| Bevel width | 1–2 mm |
| Normals | hardened |

### 4.4 Water marks
- Coffee rings, with the rim stronger. Tide lines of dried puddles on tops. Drip or tea streaks on
  verticals.
- Spots under ~3 px vanish: at ~3 mm/px they need 8–25 mm.

| Parameter | Value |
|---|---|
| Coffee rings | rim stronger |
| Tide lines | on tops |
| Drip / tea streaks | on verticals |
| Spot size | 8–25 mm at ~3 mm/px (under ~3 px vanish) |

### 4.5 Joint dust and per-part tone
- AO dust in the joints.
- ±6 % per-part tone.

| Parameter | Value |
|---|---|
| Joint dust | AO in joints |
| Per-part tone | ±6 % |

### Generic layers, metal settings
No generic layers apply to this file.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Water marks missing at the final view | spots under ~3 px | size them to 8–25 mm at ~3 mm/px (§4.4) |
| Brush lines run across the part | tangent not along the part's length | directional UV along the part's length (§4.2) |
| Edges look sharp and unbroken | no bevel | 1–2 mm bevel with hardened normals (§4.3) |

No generic problems are listed in this file. The general list is in troubleshooting.md (named here,
not linked, so this file adds no reference loop).
