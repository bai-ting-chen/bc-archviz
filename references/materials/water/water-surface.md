# Water surface (pools, still water)

## 1. Overview
The pool body: water coloured by its depth, the water surface, wind ripples.

**Use when:** the pool itself, or ripples with no cause. Ripples from a landing, impact or plunge:
[water-ripple.md](water-ripple.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. The impact ripples are written once, in their own reference,
and used here with pool settings.

```
                  WATER SURFACE (POOL BODY) — LAYER DIAGRAM
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                            │
 │   §4.1 Pool water shading (depth tint)  → shader                         │
 │   §4.2 Pool geometry (top face, diced)  → mesh                           │
 │   §4.3 Rippled sunlit pool (Ocean)      → geometry waves, micro bump     │
 │   §4.4 Opaque pool look (stylised)      → shader, only when asked        │
 │   §4.5 Thin-wall water                  → shader for open shells         │
 │ GENERIC (own reference)                                                  │
 │   Impact ripples, choppy plunge pools   → water-ripple.md                │
 └──────────────────────────────────────────────────────────────────────────┘
```

Flow:
```
   §4.2 top face of the basin (diced, smooth) ──► §4.3 Ocean waves on the same plane (short waves = caustics)
   §4.1 shader on that mesh: absorption by depth, IOR 1.333, shallow ripple bump
   §4.4 replaces the clear body only when asked; §4.5 is the same water for open shells (crowns, bubbles)
```

- Colour comes from depth (§4.1), not from a gradient map.
- The geometry carries the ripples (§4.3); the shader keeps only a millimetre-scale micro bump.

## 3. Code
`scripts/blender/materials/water/`:
- `pool_material.py`: `pool_water()` (§4.1), `thin_wall_copy(material, name)` (§4.5).
- `water_mesh.py`: `water_surface(obj, …)` (§4.2).

No control scene for the pool body yet; `scripts/controls/water/mnee_water.py` renders a water plane for caustics.

## 4. Instructions and parameters, per layer

### 4.1 Pool water shading
- `pool_water()`: Principled transmission 1, IOR 1.333, a shallow ripple bump, and **Volume
  Absorption** for the tint — depth does the colour work, so a pool reads green in the deep end and
  clear at the step without any gradient map.
- **The floor sets the pool's tone.** Water reflects little until the view grazes (Fresnel at IOR
  1.333: ~4 % at 55°, ~9 % at 65°, ~13 % at 70° incidence), so the pool's colour is mostly the floor
  seen through the body. Judge and choose the floor first.
- **To try (manual-confirmed):** **Volume Coefficients** node (absorption per channel in 1/m, from
  measured water absorption) + Volume Scatter phase **Fournier-Forand** (IOR 1.0–1.2,
  backscatter) for haze and light shafts; noise → roughness for wind patches; Gabor texture for
  directional ripples.

| Parameter | Value |
|---|---|
| Transmission | 1 |
| IOR | 1.333 |
| Tint | Volume Absorption (depth), no gradient map |
| Fresnel reflection | ~4 % at 55°, ~9 % at 65°, ~13 % at 70° incidence |
| Ripple bump | shallow |
| To try: scatter phase | Fournier-Forand, IOR 1.0–1.2 |

### 4.2 Pool geometry
- `water_surface(obj, …)`: top face only, diced, smooth (MNEE-ready; the volume still works over an
  opaque basin). Keep the waterline just under the coping.

| Parameter | Value |
|---|---|
| Faces | top face only, diced, smooth |
| Waterline | just under the coping |

### 4.3 Rippled sunlit pool (Ocean geometry, wind ripples)
- Ocean modifier on a diced plane, `wave_scale_min` >= 5 × grid spacing or the waves alias. Short
  wavelengths give the tight caustic networks; long swell does not.
- Wind ripples that carry caustics or read as shapes are geometry (the choice:
  [water-ripple.md](water-ripple.md) › Bump or geometry). Dice the surface finer, sized from the
  ripples visible in the shot, and keep only a millimetre-scale micro bump in the shader.
- **Never stretch** the ripples "because they look flat": perspective already does that.
- **A little choppiness** for crisp crests, never enough to fold the surface: check for downward faces.
- Size the swell by RMS slope, not just amplitude.

| Parameter | Value |
|---|---|
| `wave_scale_min` | >= 5 × grid spacing (cell) |
| Choppiness | a little, for crisp crests |
| Downward faces | check for them; downward faces = folds |
| Shader micro bump | millimetre scale only |
| Swell sizing | by RMS slope, not amplitude |
| Stretch | never |

### 4.4 Opaque pool look (stylisation, only when asked)
- Opaque diffuse body under an exact IOR 1.333 surface. Declare it. Near-field sky reflection is
  small (§4.1), so a reference that is near-white there is showing a pale floor through clear water.

| Parameter | Value |
|---|---|
| Surface IOR | 1.333 |

### 4.5 Thin-wall water (open shells)
- `thin_wall_copy(material, name)`: a copy of a water material with Principled Thin Wall on. It gives
  glints and rims with straight transmission, no bending.
- Use it for small open shells standing on or above the water: splash crowns, floating bubbles. A
  solid water material on an open shell traps light and glows white.
- Never as a second skin over the pool for ripples: it adds its own reflection
  ([water-ripple.md](water-ripple.md) §2).

| Parameter | Value |
|---|---|
| Thin Wall | on |
| IOR | 1.333 (from the source material) |

Generic layers, pool settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Impact ripples, choppy plunge pools, bump or geometry | [water-ripple.md](water-ripple.md) | the choice between bump and geometry is made there |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Wind ripples read artificial | a noise bump faking short ripples | dice finer, Ocean geometry carries the ripples (§4.3) |
| Ripples look over-stretched | stretching doubles what perspective already does | never stretch (§4.3) |
| Waves alias | `wave_scale_min` below 5 × grid spacing | `wave_scale_min` >= 5 × cell (§4.3) |
| Folds in the surface | downward faces | check for downward faces; a little choppiness only (§4.3) |
| Caustics too soft | long swell only | short wavelengths give the tight caustic networks (§4.3) |
| Near field too pale through clear water | a pale floor seen through the clear body | judge the floor; opaque look only as a declared stylisation (§4.1, §4.4) |

Generic problems: `references/workflow/troubleshooting.md` (not linked from this file: a link here
would close a reference loop).
