# Lighting

## 1. Overview
Router for lighting a scene in real units: which light to use, which file holds its method, and
the cheat sheet of common values. The camera and its exposure are in `references/scene/camera/camera.md`.

## 2. Layers and node-editor diagram
```
 ┌─ LIGHTING — PROCEDURE DIAGRAM ──────────────────────────────────────────┐
 │ Units         one constant: 683 lm per Blender W                       │
 │   ▼                                                                    │
 │ Environment   an HDRI world, scaled to lux ─► World Surface            │
 │   ▼                                                                    │
 │ Fixtures      IES file if specified, else lumens ─► light power (W)    │
 │   ▼                                                                    │
 │ Grey check    neutral material override ─► judge light alone           │
 │   ▼                                                                    │
 │ Atmosphere    fog or mist, when the shot has it ─► World/box Volume    │
 └────────────────────────────────────────────────────────────────────────┘
```
- Exposure is set on the camera after the lights, never by scaling lights to taste (RULES LGT_01).

## 3. Code
- `scripts/blender/scene/lighting/photometry.py`: `LM_PER_W = 683.0`, shared by lights, the HDRI world
  and the camera.
- Builders are named in each file below. Control for the units: `scripts/controls/lighting/light_units.py`.

## 4. Instructions and parameters
1. **Units.** 683 lm/W is the SI definition of the lumen (1 W of 555 nm light = 683 lm). Reading Blender
   watts through it makes a lamp in lumens, an HDRI in lux and a camera in EV100 agree. Keep each
   light's *Normalize* on and *Exposure* at 0, so watts stay lumens/683.
2. **Environment.** Light from the surroundings comes from one HDRI world: [hdri.md](hdri.md).
3. **Fixtures.** A specified fixture uses its photometric file: [ies-profiles.md](ies-profiles.md).
   Otherwise convert its lumens by light type: [artificial-light.md](artificial-light.md). Pick the type
   from the table below.
4. **Grey check.** Render once with a neutral grey override (view layer *Material Override*, albedo
   ~0.5) before judging materials. Check: light direction, falloff and contrast read as intended.
   A fault seen here is a lighting fault; fix it here, not in the materials.
5. **Atmosphere.** Fog and mist: [fog.md](fog.md).

| Source | Use for | Units and traps |
|---|---|---|
| World (HDRI) | light from the surroundings: sky, sun, a night street, a room | lux, via `world_hdri_lux` |
| Point | bulbs, any IES fixture | W for the full sphere; Radius = lens size (softness only) |
| Spot | downlights without an IES file | same power as a point; the cone only masks |
| Area | panels, coves, light boxes | Lambert emitter, power = flux; *Spread* narrows it; *Portal* only samples the world |
| Sun lamp | tests and controls only (RULES LGT_02) | W/m² |
| Emissive mesh | visible lenses, LED lines, screens | luminance in cd/m²; count the flux once |

### Cheat sheet
Starting points; set the real values from the fixture schedule or the reference and record them in
the study notes (RULES GOV_01).

| Illuminance | lux |
|---|---|
| Full sun | 80 000–100 000 |
| Overcast daylight | 10 000–20 000 |
| Dusk, just after sunset | 10–400 |
| Lit street at night | 5–30 |
| Office work plane | 300–500 |
| Living room, evening | 50–150 |

| Colour temperature | K |
|---|---|
| Candle | 1 800–2 000 |
| Warm white lamp | 2 700–3 000 |
| Neutral white lamp | 3 500–4 000 |
| Daylight lamp, noon sun | 5 000–5 600 |
| Overcast sky | 6 500 |
| Clear blue sky, dusk sky | 8 000–12 000 |

| Fixture | Output |
|---|---|
| Domestic downlight | 400–1 000 lm |
| LED cove or niche strip | 300–1 500 lm/m (low end when grazing a wall) |
| Linear office pendant | 2 000–4 000 lm/m |
| Façade or landscape flood | 1 000–5 000 lm |

- **Dusk and night:** interior lamps at 2 700–3 000 K against a sky near 10 000 K give the warm/cool
  contrast; both keep their real output, and the camera's exposure and white balance set the mood.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Lights look right but the frame is too bright or dark | exposure, not light power | set the camera's EV100 (`references/scene/camera/camera.md`) |
| A fixture lights twice as strongly as its lumens | a visible lens and an analytic light both emit | count it once ([artificial-light.md](artificial-light.md)) |
| Scene flat with materials on, fine in the grey check | materials, not light | leave the lights; fix albedo or roughness |

Problems of one light type are in that file's §5; generic render problems in troubleshooting.md.
