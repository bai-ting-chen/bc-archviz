# Lighting and camera — real units

One constant everywhere: **683 lm per Blender W** (lights, HDRI lux, camera exposure).

## Daylight
- `archviz.hdri_analyse(id, rot)` integrates the upper hemisphere → lux at strength 1 and the sun
  direction (centroid of the top 0.05 % texels). `world_hdri_lux(id, target_lux)` scales it.
  Measured lux at strength 1: golden_gate_hills 3444, kloofendal_48d_puresky 3269,
  studio_kontrast_04 1998, monochrome_studio_02 629. Targets: sunny 80 klux; studio 500 lux.
- Equirect: `u = 0.5 − atan2(y,x)/2π`, `v = elev/π + 0.5`; world Mapping rotates the lookup (Rzᵀ).
- Sun matched to the HDRI: `sun_from_direction(dir, lux)` (strength W/m² = lux/683).
- Sky Texture `MULTIPLE_SCATTERING` (5.2 name): calibrate with a white-plane render.

## Artificial light (measured to 0.2 %, `tools/controls/light_units.py`)
- **Spot/point = point-equivalent**: power is for the full sphere, the cone only masks.
  F lm in full beam a: `P = F/683 · 4π / (2π(1 − cos a/2))` → `interior.downlight(lumens, beam_deg)`.
- **Area = Lambert emitter**: `E = P/(πd²)` on axis; `spread` focuses the same power.
  Strip: `P = lm_per_m · L / 683` → `interior.led_strip(p0, p1, lm_per_m, normal, spread)`.
  For a target E at d: `P = E·π·d²/683`.
- **Emissive lens**: `L = F/(πA)` cd/m², strength = L/683 → `interior.lens_luminance`.
- Colour: `light.use_temperature`, `light.temperature` (K).
- Values that matched a night spa: cove 600 lm/m 2700 K; grazing wash ≤ 2200 lm/m; 4-head
  downlight 1000 lm 30°; pool light 1200–2500 lm; niche strips 2500 lm/m 2400 K.

## Placement and visibility
- Wall grazing: thin area strip 2–5 cm off the wall at the top, aimed ~20° in. Spots → scallops.
- Recessed fixture: `visible_camera = False` on the light (it sits in a slot).
- **Count each fixture once.** Either the lens is the source (luminance from lumens, visible to all
  rays) or the lens is decor for an analytic light → `interior.lit_once()` = `visible_diffuse` AND
  `visible_transmission` off. Visibility follows the LAST bounce: diffuse → through water arrives
  as transmission, so diffuse-off alone leaks (it turned a ceiling green).
- Underwater lights: aimed spots along the pool; a Lambert lens near the surface throws most light
  out onto the ceiling.

## Camera
- `physical_camera(cam, iso, f, shutter, focal)`: `EV100 = log2(N²/t) − log2(ISO/100)`,
  `exposure = log2(683/1.2) − EV100`; same f-stop drives DOF. Typical EV100: sun 15, overcast
  12–13, daylit interior 9, studio 10–11, dim night interior ~5 (ISO 800 f/8 1/4 s).
- `straighten_verticals(cam)`: level + `shift_y = lens·tan(pitch)/sensor_width`.
- White balance: `view_settings.use_white_balance`, `white_balance_temperature` = colour shown
  neutral — **lower = cooler**. 3000 K lights + WB 4300 K kept the warmth of a MIR reference.

## Recreating a reference
### Camera
1. `refmatch.py grid ref.png out.png --step 25` → read the horizon (where parallel horizontal
   edges converge) and the vanishing point of the dominant direction. Crop and zoom regions
   (Pillow) to read edges; one full-frame look misreads thin members.
2. Eye height without a known size: a vertical element standing on the floor splits at the
   horizon — `(top − horizon) / (horizon − base)` in pixels = `(H − eye) / eye`. Pick a plausible
   H (clear height, rail, door) and the eye follows; its width/height ratio then sizes it.
3. Focal: assume a common archviz lens, then check proportions in the overlay; parallel lines
   in one direction alone cannot fix the focal.
4. Level camera + lens shift (parallel verticals). **Shift trap:** with `sensor_fit =
   HORIZONTAL`, `shift_x/shift_y` are fractions of the frame **width** even on a portrait frame,
   and +shift_x moves the frame right, so the principal point appears left:
   `shift_x = −(vp_x − W/2)/W`, `shift_y = (horizon_y − H/2)/W` (pixels from the top).
   Verify by projecting a far point on the axis with `world_to_camera_view` — it must land on
   the measured vanishing point. Never trust the first framing render by eye.
5. `archviz.framing_render()` + `refmatch.py pair --overlay`; move geometry, not the camera,
   once the vanishing point and one height match.

### Camera from a repeated element (colonnade, mullions, bays)
Code: `tools/refsolve.py readings.json` (and `Solve.floor_pt / plane_pt / pt_at_z / fit_circle /
blender()` from a study script). It reproduced a hand solve to 0.6 px of horizon.
Read the base and top of every repeat at full resolution (ticked 2x crops, not the downscaled
frame). Then:
- Lines through the bases and through the tops meet at the façade vanishing point; its y is
  the horizon (level camera).
- Apparent height h ∝ 1/depth, so equal steps in 1/h prove an equal pitch, and the pitch
  (or one known size) fixes the scale. Eye height = H · (y_base − horizon)/h, which is the same
  for every repeat — a check on the readings.
- Focal is the weak unknown. The ellipse of a round base gives depression angle ≈
  asin(sagitta / half-width), so f ≈ (y_base − horizon)/tan(angle). Per-column values scattered
  2470–3900 px on one image: take a plausible lens, then judge by the overlay.
- With f, eye and horizon fixed, image → plan is two formulas. A floor point is at depth
  `Z = f·eye/(y − horizon)`, `X = (x − cx)·Z/f`. A point on a known vertical plane: intersect
  the pixel ray with that plane. Read wall bases, openings and lamps this way. A residual of
  the repeats from one straight line (≤ 0.07 m on a 4.5 m pitch) means the solve holds.
- Keep the solve as a small script in the study: every later geometry question becomes one call.

### Geometry readings
- When a reading fits one cue but not the structure (a beam that "ends" at another beam's
  soffit, a member too thin to span), prefer the structurally plausible reading — a downstand
  beam runs to the slab — and fix the light instead. If still ambiguous, state the reading and
  let the user correct it.
- A deep element casting shade over a region that is bright in the reference means either the
  geometry or the light position is wrong: check both before adding light.
- **What stays visible decides the reading.** A dark band under a slab read as a downstand hid
  three pendant globes that the reference shows. Re-solved with rays, it is a step UP in the
  ceiling, and the band is the wall head seen inside the recess. Before keeping any member, check
  that it does not cover something visible in the reference.
- **Fit a curve where it meets its neighbour.** A free circle fit through floor points pushed a
  drum in front of the wall, over a window. Constraining it to meet the wall plane at the pixel
  where it visibly emerges fixed it, and its shoulder then explained a light strip.
- Open vs roofed: a region that is bright in the reference but black in the render is usually
  roofed in the model — but cut the roof only where the reference shows open sky. Cutting it too
  far lit the drum from above.

### Light, region by region
1. `refmatch.py patches ref.png regions.json render.png` (regions.json in the study folder:
   `{"name": [x0, y0, x1, y1], …}` in 0..1, y from top; ~10 regions: each lit surface type,
   the shadow side, floor near/far, the background). Keep a table of render/ref ratios per
   iteration; aim for equal ratios first, then exposure.
2. Read where the light comes from before placing any:
   - **Visible fixtures may face away.** A lamp head seen from behind (dark back) lights the far
     room, not the foreground.
   - **Cast shadows give direction.** Shadow width w thrown by a member of depth d onto the
     surface it hangs from → source elevation ≈ atan(d / w), on the opposite side.
   - A region brighter than anything its visible sources can reach → an **out-of-frame source**
     (behind or beside the camera). Add it, check it is outside the frustum (project its
     position), and **declare it** to the user — it is not in the reference image.
   - Check the ray from a candidate source to the target clears intervening members before
     trusting it (a beam can shadow the bay you are trying to light).
3. Spots/floods: a wide cone aimed at a ceiling also lights the column and walls in front of
   it; when one element is too bright, find which cone it sits in (angle from the axis) and
   narrow or re-aim that light rather than dimming everything.
4. Graded references (flat, sepia): AgX *Base Contrast*, white balance near the lamp
   temperature, tone the material albedo warm/cool before touching grading. The look follows
   the reference, not habit: a crisp dusk reference matched under *Medium High Contrast*, and
   Base Contrast read hazy.
5. **Glass and what it shows.** Façade glass reflects only ~5–8 % at 30–50° incidence, so
   glazing that reads bright in the reference is lit from behind. White sheers that read ~4x the
   surrounding stone need ~3000 lux on their backs. A 60 klm room wash gave ~14 cd/m² and stayed
   dark, so model the backlight as a wash ~1 m behind the sheer and **declare** it (rooms
   beyond, not in the image). For the reflection itself, mirror the camera ray in the glass
   normal, then pick the HDRI rotation from luminance by azimuth: trees on the horizon band,
   bright sky at 20–40° elevation for upper floors. Rotate the HDRI, not the glass.
6. Exposure last (RULES 7). When every region is off by the same ratio, that is the exposure
   step, so take it then.

## Misc
- Area lights emit along local −Z. With rotation (θ, 0, 0) the beam goes along
  (0, sin θ, −cos θ): −90° faces −Y, 145° points up and toward +Y. Print the world direction
  after creating the light.
- Pendant globes: a solid glass sphere is a lens ball. Give it a 3 mm Solidify shell, IOR 1.5
  and roughness ~0.3 so it reads as lit glass (`lookdev.glass_shell(objs)`). The bulb is a point light with
  `visible_camera = True`; hide the bulb mesh so the fixture counts once.
- Backdrop that lights nothing: Mix(HDRI, white Background, Light Path *Is Camera Ray*); under AgX
  display-white needs ~4/2^exposure.
- AgX rolls whites off: match targets on the written PNG, not linear values.
