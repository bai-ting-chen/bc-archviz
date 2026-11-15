# HDRI

## 1. Overview
An HDRI world as the light from the surroundings: daylight, dusk, night or an interior map.
Choosing the map, measuring it, rotating it and scaling it to lux.

## 2. Layers and node-editor diagram
```
 ┌─ HDRI — PROCEDURE DIAGRAM ──────────────────────────────────────────────┐
 │ Choose        shortlist by tag, judge on the equirect                  │
 │   ▼                                                                    │
 │ Measure       lux at strength 1, brightest direction, sun share        │
 │   ▼                                                                    │
 │ Rotate        Mapping Z rotation ─► Environment Texture Vector         │
 │   ▼                                                                    │
 │ Scale         target lux / measured lux ─► Background Strength         │
 │   ▼                                                                    │
 │ Fallback      Sky Texture, only when no map fits (declared)            │
 └────────────────────────────────────────────────────────────────────────┘
```
- The HDRI is the sole natural light: no sun lamp beside it (RULES LGT_02).

## 3. Code
- `scripts/blender/scene/lighting/hdri.py`, also on the `archviz` facade:
  - `hdri_analyse(hdri_id, rotation_deg)`: lux at strength 1 and the brightest direction.
  - `world_hdri_lux(hdri_id, target_lux, rotation_deg, visible)`: builds the world at a target lux.
  - `world_hdri(hdri_id, strength, rotation_deg, res)`: the raw world.
  - `sun_from_direction(direction, strength_lux)`: a sun lamp for scenes with no HDRI (tests, controls).
- Maps are read from the study library, `library/polyhaven/hdris/<id>` (RULES AST_03).

## 4. Instructions and parameters
1. **Choose.** Shortlist by tag (Poly Haven API `api.polyhaven.com/assets?t=hdris`), then judge on the
   equirect, not the thumbnail sphere: tone-map a 1024 px strip and draw the horizon line. All of
   these must fit in one map, so shortlist widely:
   - the condition (clear, overcast, dusk, night, interior);
   - the height of the brightest source (rotation changes only its azimuth);
   - the horizon content and how high it reaches. Content metres from the HDRI camera fills the
     sky and leaves nothing bright to reflect.
   Check: the map's horizon content sits where the shot needs it. A viewer at eye height h_e
   looking through glazing from z0 to z1 sees the horizon at (h_e − z0)/(z1 − z0) of the glass height.
2. **Measure.** `hdri_analyse` on the chosen map; every file differs, so measure, never remember.
   When hard shadows or caustics matter, also measure the **sun share**: horizontal irradiance of
   the texels within ~1.5° of the sun centroid against the whole upper hemisphere.
   Check: the share fits the shot (table). Undo: choose another map; a weak sun is not repaired
   with a lamp (RULES LGT_02).
3. **Rotate.** Cycles equirect: `u = 0.5 − atan2(y, x)/2π`, `v = elev/π + 0.5`. To put equirect
   column u at world azimuth a (degrees from +X): Mapping Z rotation `= 360·(0.5 − u) − a`.
   Check: `hdri_analyse(id, rotation)` returns the wanted azimuth.
4. **Scale.** `world_hdri_lux(id, target_lux, rotation)`; target from the cheat sheet in
   `references/scene/lighting/index.md` or from the reference.
5. **Fallback.** Sky Texture `MULTIPLE_SCATTERING`, calibrated with a white-plane render; say that it
   was used (RULES LGT_02).

| Sun share | Reads as |
|---|---|
| ~70–90 % | unclipped clear sky: crisp shadows and caustics |
| under ~60 % | hazy, partly cloudy or clipped: soft shadows, washed caustics |

- **Backdrop that lights nothing:** Mix(HDRI, white Background, Light Path *Is Camera Ray*); under AgX,
  display white needs ~4/2^exposure.
- **Soft backplate against a crisp model:** the softness is in the photo, so a sharper map does not
  help; the fix is on the camera (`references/scene/camera/camera.md`).

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Soft shadows under a "clear" sky | low sun share or a clipped disc | measure the share; choose another map (step 2) |
| Sun at the wrong height | rotation only turns the azimuth | choose a map with that elevation (step 1) |
| Glass and water reflect nothing bright | horizon content fills the sky | choose a map shot from an open viewpoint (step 1) |
| Scene brightness changes between maps | strength reused instead of lux | scale each map with `world_hdri_lux` (step 4) |

Glazing that reads darker than a reference: `references/materials/glass/glass.md`. Generic render
problems are in troubleshooting.md.
