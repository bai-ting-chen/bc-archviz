# Vegetation

## 1. Overview
Two looks share this file. Leaf litter and foliage are small leaves scattered over surfaces; grass
and meadow cover terrain as a sward of blade clumps. Both are instanced: a scatter places copies of
a leaf or clump and masks where they land. The bare soil that shows through the grass comes from the
ground shader, not from this file (ground.md, plain-text neighbour).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with vegetation settings.

```
                                 VEGETATION
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                          GENERIC (own reference)            │
 │ 1 Leaf-litter scatter → instances      Per-instance tone → variation.md   │
 │ 2 Meadow scatter      → instances      Bare soil → ground.md (plain text) │
 │ 3 Blade material      → grass shading                                     │
 └───────────────────────────────────────────────────────────────────────────┘
   node-editor flow, what each step drives
   leaf litter:  faces ─► Z < limit AND patch noise ─► Instance on Points (1)
                 ─► Object Info › Random tone (generic)
   meadow:       terrain ─► species patch × shared bare-soil × pad clearance
                 × camera frustum + distance ─► instances (2)
   blades:       instanced blade geometry ─► blade material (3)
```

- **Leaf litter and grass are separate setups.** Each one is a scatter; the grass blades take the
  blade material (3), and per-instance tone comes from the generic layer.
- **One object per species** for the meadow (§4.2).

## 3. Code
- `scripts/blender/materials/vegetation/`: `vegetation.py` (entry point `blade_material`, imported
  from `blade_build.py`; config in `blade_config.py`, wet and dew in `blade_wet.py` and
  `blade_dew.py`).
- `scripts/blender/scene/environment/`: `scatter.py` is the import point for leaf litter and meadow.
  Leaf litter uses `scatter_objects.py` (`scatter`); the meadow uses `scatter_asset.py`
  (`load_scatter_on_surface`), `meadow_graph.py` (`meadow_layer_group`) and `meadow_objects.py`
  (`meadow_layer`, `frustum_tangents`).
- Per-instance tone: `scripts/blender/effects/variation.py` (`random_tone_material`).
- Control: `scripts/controls/material/vegetation_graph_check.py` (deterministic graph and geometry
  baseline).

## 4. Instructions and parameters, per layer

### 4.1 Leaf-litter scatter (instances)
- One GN group: Distribute Points on Faces, with selection = Z below a limit AND a noise patch
  threshold, then Instance on Points with random rotation and scale.
- Per-instance tone via Object Info › Random, from the generic layer (variation.md).
- **The patch threshold is knife-edge.** A hair too low blankets the surface; a hair too high clears
  it. Bisect it against a render rather than reasoning about it.

| Parameter | Value |
|---|---|
| Patch threshold | knife-edge: bisect against a render |
| Selection | Z below a limit AND the noise patch |
| Instance transform | random rotation and scale |

### 4.2 Grass and meadow scatter (instances)
- Use `scatter.meadow_layer_group(scatter.load_scatter_on_surface())`: Blender's own *Scatter on
  Surface* (native, Poisson or random, collection + Pick Instance), wrapped with mask fields:
  - species patch noise;
  - a **shared** bare-soil noise, the same 4D noise the ground shader uses (`terrain.BARE_W`), so
    bare spots show earth;
  - clearance from the pad;
  - the **camera frustum + distance**: only what the camera can see; the crest hides the rest.
- One object per species. Align Rotation off (grass grows up, gravitropism), with a small random lean.
- **Check the units of each vendor volume against a known plant height before anything else.** One
  grass volume was in mm where its tree volume was cm; read in cm, clover came out 1 m tall.
- **Density is set by clump size.** A few-blade lawn clump needs ~200 /m² to close the sward (30 /m²
  left mostly soil).
- **Memory:** ~0.5–1 M instances render fine on 8 GB. Unique meshes cost memory; instances barely do.
- **Species mix reads as pasture:** a dense low carpet, tuft drifts, broad-leaf (clover) patches, and
  sparse seed heads and flowers.

| Parameter | Value |
|---|---|
| Density, lawn clump | ~200 /m² (30 /m² left mostly soil) |
| Instance count | ~0.5–1 M renders fine on 8 GB |
| Align Rotation | off |
| Lean | small, random |
| Object count | one per species |

### 4.3 Blade material (grass shading)
- `materials.vegetation.vegetation.blade_material`: Principled plus Translucent. Green leaf transmits
  a little light at the 550 nm peak and less across the rest of the visible range.
- Per-instance value and a patchy straw or dry mix on the instance location (RULES MAT_05, MAT_06).
- **Canopy albedo is low.** A grass canopy's visible albedo is only ~0.05–0.1, and under a
  high-contrast AgX look it sinks. Choose a softer look rather than brightening the albedo.

| Parameter | Value |
|---|---|
| Leaf reflectance R (green) | ~0.10–0.15 |
| Leaf transmission T (green) | ~0.05–0.10 at 550 nm, lower across the rest of the visible |
| Roughness | ~0.45 (waxy cuticle) |
| Per-instance value | 0.8–1.15 |
| Visible canopy albedo | ~0.05–0.1 |

### Generic layers, vegetation settings
| Layer | Reference | Vegetation note |
|---|---|---|
| Per-instance tone | [variation.md](../../effects/variation.md) | `random_tone_material` on the leaf-litter instances (§4.1) |
| Bare soil under the grass | ground.md (plain text) | the same 4D noise as the meadow mask (§4.2) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Leaf litter blankets the whole surface | patch threshold a hair too low | bisect the threshold against a render (§4.1) |
| Leaf litter clears the surface | patch threshold a hair too high | bisect the threshold against a render (§4.1) |
| Clover about 1 m tall next to the grass | one vendor volume in mm, another in cm | check every volume's units against a known plant height (§4.2) |
| Lawn sward shows mostly soil | ~30 /m² instead of a clump density that closes the sward | ~200 /m² for a few-blade lawn clump (§4.2) |
| Grass costs too much memory | unique meshes per instance | use instances; they cost little (§4.2) |
| Grass canopy sinks dark under AgX | visible albedo only ~0.05–0.1 | choose a softer look; do not brighten the albedo (§4.3) |

Generic problems that show up in any material are in troubleshooting.md.
