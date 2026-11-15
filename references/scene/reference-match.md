# Reference match

## 1. Overview
Recreating a reference image: solving its camera, reading geometry through that camera, matching
the light region by region, and setting exposure last (RULES RES_02).

**Use when:** a reference photo or render is to be matched. A camera for a new view is in
`references/scene/camera/camera.md`.

## 2. Layers and node-editor diagram
```
 ┌─ REFERENCE MATCH — PROCEDURE DIAGRAM ───────────────────────────────────┐
 │ Camera        horizon, vanishing point, eye height, focal, shift       │
 │   ▼                                                                    │
 │ Geometry      read members and openings through the fixed camera       │
 │   ▼        ▲                                                           │
 │ Light         region ratios render/reference, made equal               │
 │   ▼                                                                    │
 │ Exposure      one step, when every region is off by the same ratio     │
 └────────────────────────────────────────────────────────────────────────┘
```
- Geometry and light go back and forth: a lit render shows which reading is wrong. A failed
  camera check is fixed before anything else.

## 3. Code
Host side, MCP venv python (numpy, Pillow):
- `scripts/review/reference_match.py grid | pair`: reading grid, side-by-side or overlay.
- `scripts/scene/reference_camera.py readings.json`: camera from a repeated element
  (`ReferenceCameraSolve`: `pixel_to_floor`, `pixel_to_facade_plane`, `pixel_to_height`, `fit_circle`,
  `blender_camera_settings()`).
- `scripts/rhino/project_edges.py` (in Rhino through Rook) with `scripts/scene/edge_overlay.py`: the
  model's edges drawn over the reference through the solved camera.
- In Blender: `archviz.framing_render(root, path)`.

## 4. Instructions and parameters
1. **Camera.** Needs: the reference image. Gives: horizon, vanishing point, eye height, focal, shift.
   1. `reference_match.py grid ref.png out.png --step 25`; read the horizon (where parallel
      horizontal edges converge) and the vanishing point of the dominant direction. Read edges on
      zoomed crops; one full-frame look misreads thin members.
   2. Eye height without a known size: a vertical element standing on the floor splits at the
      horizon, `(top − horizon)/(horizon − base)` in pixels `= (H − eye)/eye`. Pick a plausible H.
   3. Focal: assume a common lens (`references/scene/camera/camera.md`), then check proportions in
      the overlay; parallel lines in one direction alone cannot fix the focal.
   4. Level camera with lens shift. With `sensor_fit = HORIZONTAL`, shifts are fractions of the
      frame **width**, also on a portrait frame: `shift_x = −(vp_x − W/2)/W`,
      `shift_y = (horizon_y − H/2)/W` (pixels from the top).
   5. **Repeated element** (colonnade, mullions, bays): read base and top of every repeat at full
      resolution and run `reference_camera.py`. Lines through the bases and through the tops meet
      at the façade vanishing point; apparent height h ∝ 1/depth, so equal steps in 1/h prove an
      equal pitch; eye height `= H·(y_base − horizon)/h` must be the same for every repeat. The focal
      is the weak unknown: take a plausible lens and judge by the overlay.
   Check: a far point on the axis projected with `world_to_camera_view` lands on the measured
   vanishing point; the model's edges overlay the reference (`project_edges.py`, `edge_overlay.py`);
   `framing_render` with `reference_match.py pair --overlay`. Once the vanishing point and one height
   match, the camera is fixed: move geometry, not the camera.
2. **Geometry.** Needs: the fixed camera. A floor point is at depth `Z = f·eye/(y − horizon)`,
   `X = (x − cx)·Z/f`; a point on a known vertical plane is the pixel ray cut by that plane.
   - Readings near the horizon swing metres per pixel. Trust points far from it, and when two
     readings disagree, keep the better-conditioned one.
   - Prefer the structurally plausible reading, and check that no member covers something the
     reference shows. If still ambiguous, state the reading and let the user correct it.
   Check: repeats fall on one straight line in plan.
3. **Light.** Needs: camera and geometry. Measure every round as the look round in validation.md;
   this step says what to change when the region ratios disagree.
   1. Read where the light comes from before placing any: cast shadows give direction (a member of
      depth d throwing a shadow of width w puts the source at elevation ≈ atan(d/w)); a region
      brighter than its visible sources can reach means a source outside the frame. Add it, check
      it is outside the frustum, and declare it.
   2. When one element is too bright, find the light it sits in and narrow or re-aim that light.
   3. Graded references: choose the AgX look from the reference's contrast, and tone the material
      albedo before touching grading.
   Check: the look round's ratio criterion (validation.md).
4. **Exposure.** Needs: equal ratios. The common ratio is the exposure step
   (`references/scene/camera/camera.md`). If the ratios are unequal, go back to step 3.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Framing far off after setting the shift | shift taken as a fraction of the height | width formulas (step 1.4) |
| Depth readings disagree by metres | points read near the horizon | use well-conditioned points (step 2) |
| Overlay fits one bay, drifts on the others | focal assumed wrong | try another plausible lens (step 1.5) |
| A region black that is bright in the reference | roofed in the model, or shaded by a misread member | check sky access and the member against the reference (step 2) |
| One region stays too dark at any exposure | an out-of-frame source is missing | add and declare it (step 3.1) |
| Rhino viewport capture does not match the solve | captures ignore the requested size, so a shifted view captures wrong | use the edge overlay (step 1 check) |

Generic render problems are in troubleshooting.md.
