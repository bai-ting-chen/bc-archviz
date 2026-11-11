# Glass relief

## 1. Overview
Glass whose surface is shaped on purpose: patterned, cast and pressed glass, the inner faces of glass
block, wavy acrylic. The relief is a height field modelled as geometry; this file is how to shape it.
Sizing a relief for the light pattern it throws is in [caustics.md](../../effects/caustics.md) step 2.

**Use when:** the relief is large enough to see at the shot's distance. Ribs too fine to resolve are
[anisotropy.md](../../effects/anisotropy.md); the slight wobble of flat glazing is `glass.md` §4.2.

## 2. Layers and node-editor diagram
```
 ┌─ GLASS RELIEF — PROCEDURE DIAGRAM ───────────────────────────────────────┐
 │ Geometry or blur   resolved at the shot ─► geometry; else anisotropy     │
 │   ▼                                                                      │
 │ Shape              wave sum or pattern family ─► height field            │
 │   ▼                                                                      │
 │ Border             fade to flat, round the edges ─► mesh                 │
 │   ▼                                                                      │
 │ Variants           several reliefs, turned and flipped ─► instances      │
 │   ▼                                                                      │
 │ Finish             clear glass base, satin roughness ─► Principled       │
 │   ▼                                                                      │
 │ Light pattern      only if it carries the shot ─► caustics.md step 2     │
 └──────────────────────────────────────────────────────────────────────────┘
```
- Off switch: the flat pane is the relief off; keep it as a second mesh or a zero-height variant.

## 3. Code
No builder: the relief is modelled geometry. The glass on it is `materials.glass.glass.clear_glass`.
The numpy preview of the thrown light is described in caustics.md step 2.

## 4. Instructions and parameters
Table values are starting points; size them from the shot (RULES MAT_03) and record the final values
in the study notes (RULES GOV_01).

### Step 1. Geometry or blur
- Model the relief as geometry. A bump or normal map gives no parallax, and in LuxCore it leaves dark
  seams (luxcore.md).
- Relief below a pixel at the final view is not modelled (RULES MAT_04): use directional roughness.

### Step 2. Shape the height field
- **Sum many waves, never one.** A single sine throws one bright line per ridge, repeated per unit.
  Sum about 12 waves with random directions; a mild vertical stretch reads as poured glass.
- **Cast glass is multi-scale:** soft folds, ridged creases, and only a trace of fine crinkle. Strong
  fine crinkle reads as squiggles.
- **Pattern families** (trade names Wave, Iceberg, Bubble, Diamond, Pristal, Quadra):
  - *Wave*: a few long cosines. Mixing horizontal and diagonal crests 1:1 across a wall breaks any
    single direction.
  - *Iceberg*: ridged noise, h = −√(f² + (0.08·rms)²) of a sum of broad cosines; crisp crossing lines.
  - *Diamond, Pristal, Quadra*: prisms, sharp-edged repeating patches.
- A small slope still reads from inside: 0.5° of deflection moves a tree 30 m away by 25 cm.

| Parameter | Value |
|---|---|
| Waves in the sum | ~12, random direction |
| Wavelength λ | log-uniform over the chosen range |
| Amplitude | ∝ λ^0.8, scaled to the target RMS slope |
| Depth envelope | slow, 1 ± 0.45 |
| Cast glass, soft folds | λ 8–40 cm |
| Cast glass, crinkle | very weak |

### Step 3. Border and edges
- Fade the relief to flat at the border of each unit or pane, so it meets the frame, the joint or the
  plain body cleanly.
- Straight features act as cylindrical lenses: a short fade or a tight edge radius draws a bright
  straight outline. Fade wide and use larger radii.

| Parameter | Value |
|---|---|
| Border fade | ≥ 25 mm, to flat |

### Step 4. Variants
- One relief repeated shows its tile. Make several reliefs as block definitions and place them at
  random with 180° turns and flips, instanced.

| Parameter | Value |
|---|---|
| Reliefs | ~16 (64 looks with turns and flips) |

### Step 5. Finish
- Clear glass base on the mesh. A slight roughness gives cast glass its satin haze; polished pressed
  glass stays at 0.

| Parameter | Value |
|---|---|
| Roughness, cast faces | ~0.05 |

### Step 6. Light pattern
- If the pattern the glass throws on a floor or wall carries the shot, size λ and slope from the
  receiver distance and render in LuxCore: caustics.md step 2 (RULES REN_03).

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Clear glass base | `glass.md` §4.1 | the same builder, white |
| Directional blur | [anisotropy.md](../../effects/anisotropy.md) | relief below a pixel (step 1) |
| Light pattern | [caustics.md](../../effects/caustics.md) | sizing and engine (step 6) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Relief reads as squiggles | strong fine crinkle | keep the crinkle very weak (step 2) |
| One bright line per ridge, repeated per unit | one frequency | sum ~12 waves (step 2) |
| Hard edge or bright square outline round each unit | no border fade, or a short one | fade ≥ 25 mm, larger radii (step 3) |
| The same shape repeats across the wall | one relief | variants with turns and flips (step 4) |
| Cast glass looks like polished crystal | faces fully glossy | roughness ~0.05 (step 5) |
| Dark seams, no depth in the relief | normal map instead of geometry | model it (step 1) |

Generic problems: troubleshooting.md.
