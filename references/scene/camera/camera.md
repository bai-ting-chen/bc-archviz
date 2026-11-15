# Camera

## 1. Overview
The render camera: choosing the view, lens and parallel verticals, physical exposure, white
balance and depth of field.

**Use when:** setting a camera for a new view. Solving the camera of a reference image is in
`references/research/reference-match.md`.

## 2. Layers and node-editor diagram
```
 ┌─ CAMERA — PROCEDURE DIAGRAM ────────────────────────────────────────────┐
 │ View          station point, eye height, lens                          │
 │   ▼                                                                    │
 │ Verticals     level the camera ─► lens shift                           │
 │   ▼                                                                    │
 │ Exposure      ISO, f-stop, shutter ─► EV100 ─► view exposure           │
 │   ▼                                                                    │
 │ White balance temperature shown neutral ─► view settings               │
 │   ▼                                                                    │
 │ Depth of field  same f-stop, focus distance ─► camera DOF              │
 └────────────────────────────────────────────────────────────────────────┘
```
- Render settings come before the camera: `render_setup` resets the view exposure.

## 3. Code
- `scripts/blender/scene/camera/camera.py`, also on the `archviz` facade:
  - `use_camera(name, lens)`: makes a camera active.
  - `physical_camera(cam_obj, iso, fstop, shutter_s, focal_mm, sensor_mm, focus_distance, dof)`: lens,
    exposure and depth of field from one real triple.
  - `straighten_verticals(cam_obj)`: levels the camera and recovers the framing with lens shift.
- `scripts/blender/scene/lighting/photometry.py`: `ev100(iso, fstop, shutter_s)`.

## 4. Instructions and parameters
1. **View.** Decide what the image is about, then place the camera where a person could stand.
   Check against the list below before going on. A locked-off, level camera is the default.
2. **Verticals.** `straighten_verticals(cam)`: level, then `shift_y = lens·tan(pitch)/sensor_width`
   (RULES LGT_01). Check: vertical edges at the frame's left and right are parallel.
3. **Exposure.** `physical_camera`: `EV100 = log2(N²/t) − log2(ISO/100)`,
   `exposure = log2(683/1.2) − EV100`. Pick the triple a photographer would use for that light
   (table); on a tripod, keep a mid aperture and move shutter or ISO. From a measured illuminance
   E instead: `EV100 = log2(E_lux / 2.5)`. Check: a mid-grey surface lands mid-range in the written PNG
   (RULES VAL_03).
4. **White balance.** `view_settings.use_white_balance`, `white_balance_temperature` = the colour
   shown neutral; lower is cooler. Setting it above the lamp temperature keeps warmth in the image.
   Move the temperature only and leave `white_balance_tint` at 10. Check: the hue of the whole frame,
   not one patch.
5. **Depth of field.** Off or deep for most architecture. Use a little when a soft photographed
   backplate makes a crisp model read cut out: focus slightly in front of the subject and keep
   EV100 by the shutter. Check: edge widths of a model edge and a backplate edge are close.

**View checklist**
- The subject reads in silhouette; foreground, middle and background give depth.
- The horizon is level; no edge of the subject runs along a frame edge or meets a corner.
- Eye height is a person's unless the view is meant as aerial or low.
- The lens is chosen, not left at a default; very wide lenses stretch the frame edges.
- The aspect ratio matches the delivery format.

| Lens (36 mm sensor) | Use |
|---|---|
| 18–24 mm | tight interiors; watch edge stretch |
| 24–35 mm | interiors and street-level exteriors |
| 35–50 mm | exteriors with natural proportions; details in context |
| 70–135 mm | distant exteriors, compressed façades, details |

| Eye height | m |
|---|---|
| Standing | 1.5–1.7 |
| Seated | 1.1–1.2 |

| Condition | EV100 | A workable triple |
|---|---|---|
| Bright sun | 15 | ISO 100, f/16, 1/125 |
| Overcast exterior | 12–13 | ISO 100, f/8, 1/60 |
| Dusk exterior, lit windows | 6–8 | ISO 100, f/8, 1 s |
| Daylit interior | 9 | ISO 200, f/5.6, 1/30 |
| Interior at ~400 lux | 7 | ISO 400, f/5.6, 1/15 |
| Dim night interior | ~5 | ISO 800, f/8, 1/4 |
| Night street | 3–5 | ISO 400, f/5.6, 1/2 s |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Render white, or exposure ignored | `render_setup` called after `physical_camera` | camera after render settings (§2) |
| Framing far off after a lens shift | with `sensor_fit = HORIZONTAL`, shifts are fractions of the frame width, also on portrait frames | recompute the shift; probe with `world_to_camera_view` |
| Scripted camera faces the wrong way, or a huge shift | `matrix_world` stale after a scripted rotation | `view_layer.update()` first (done in `straighten_verticals`) |
| Solved shifts lost | `physical_camera` resets lens and sensor fit | re-apply the shifts after it (step 3) |
| Whole frame pink or green after warming | tint moved off 10 | temperature only (step 4) |
| Image too cold after white balance | temperature set below the lamp's | raise it above the lamp temperature (step 4) |
| Model crisp against a soft backplate | photographed softness in the HDRI | slight depth of field (step 5) |

A camera from a Rhino named view: `references/scene/pipeline.md` › Phase 2. Generic render
problems are in troubleshooting.md.
