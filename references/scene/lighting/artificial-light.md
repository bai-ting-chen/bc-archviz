# Artificial light

## 1. Overview
Lamps and fixtures built from Blender lights and emissive meshes, with power set from lumens.

**Use when:** the fixture has no photometric file. With an IES or LDT file, use `ies-profiles.md`.

## 2. Layers and node-editor diagram
```
 ┌─ ARTIFICIAL LIGHT — PROCEDURE DIAGRAM ──────────────────────────────────┐
 │ Type          point, spot, area or emissive mesh                       │
 │   ▼                                                                    │
 │ Power         lumens ─► W (lights) or cd/m² ─► Emission Strength       │
 │   ▼                                                                    │
 │ Colour        temperature in K ─► light Temperature / Blackbody        │
 │   ▼                                                                    │
 │ Count once    lens or analytic light carries the flux, not both        │
 │   ▼                                                                    │
 │ Sampling      per-light Cycles settings                                │
 └────────────────────────────────────────────────────────────────────────┘
```

## 3. Code
- `scripts/blender/scene/lighting/artificial.py` (module `scene.lighting.artificial`):
  - `downlight(name, location_m, lumens, beam_deg)`: a spot pointing down; lumens inside the beam.
  - `led_strip(name, p0, p1, lm_per_m, normal=…, spread_deg=…)`: a thin area light along a run.
  - `panel_light(name, location_m, rotation_rad, size, lumens)`: a rectangular area light.
  - `emitter(name, luminance_cd, kelvin)`: an emissive material in cd/m²; `lens_luminance(lumens, area_m2)`.
  - `lit_once(objs)`: takes decorative lenses out of diffuse and transmission paths.
- Control: `scripts/controls/lighting/light_units.py` (formulas measured to 0.2 %).

## 4. Instructions and parameters
1. **Type.** From the table in `references/scene/lighting/index.md`.
2. **Power.** From the lumens on the fixture schedule (table). Check: illuminance on a white
   Lambert patch against a hand calculation.
3. **Colour.** `light.use_temperature` and `light.temperature`; values in the index cheat sheet.
   White balance is a camera setting, not a light colour.
4. **Count once** (RULES LGT_01). Either the lens is the source (luminance from lumens, visible to all
   rays), or the lens is decor for an analytic light: then `lit_once()` on the lens. Visibility
   follows the last bounce: a diffuse ray that passes through water or glass arrives as
   *transmission*, so turning diffuse off alone still leaks. A recessed analytic light gets
   `visible_camera = False`.
5. **Sampling.** Keep *Multiple Importance* on for area lights and glossy floors; the light tree
   (on by default) keeps many fixtures from turning into noise; *Light Linking* limits what a light
   reaches. *Shadow Caustics* is not a caustics method here ([caustics.md](../../effects/caustics.md)).

| Light | Power from lumens F |
|---|---|
| Point | `P = F/683` (W for the full sphere) |
| Spot, full beam angle a | `P = F/683 · 4π / (2π(1 − cos a/2))`; the cone only masks |
| Area | `P = F/683`; on axis `E = P·683/(π d²)`; *Spread* focuses the same power |
| Strip of length L | `P = lm_per_m · L / 683` |
| Area, for a target E at distance d | `P = E·π·d²/683` |
| Emissive lens of area A | `L = F/(π A)` cd/m²; Emission Strength = L/683 |

- **Wall wash or graze:** a linear source along the wall. Closer and steeper gives more relief and
  falloff. A row of spots gives scallops; use spots only when scallops are wanted.
- **Area-light direction:** they emit along local −Z; print the world direction after creating one.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Spot far dimmer than its lumens | power set as F/683 without the cone factor | spot formula (step 2) |
| Colour cast or extra light through water or glass | a decorative lens seen by transmission rays | `lit_once()` (step 4) |
| Lamp or bulb invisible in the render | `visible_camera` off, or the type hides it | check `visible_camera`; confirm in a small control (step 4) |
| Unwanted scallops on a washed wall | spots used as wall washers | a linear source (wall wash) |
| Light power changes with its size | *Normalize* off | keep it on (`references/scene/lighting/index.md`, step 1) |

Generic render problems are in troubleshooting.md.
