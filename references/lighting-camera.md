# Lighting and camera — real units

One constant everywhere: **683 lm per Blender W** (lights, HDRI lux, camera exposure).

## Daylight
- **Matching an HDRI to a reference** (RULES 8a). Shortlist by tags from the Poly Haven API
  (`api.polyhaven.com/assets?t=hdris`: overcast/clear, forest/park/urban...), then judge on the
  equirect itself, not the thumbnail sphere: tone-map a 1024 px strip in Blender, draw elevation
  lines at 0° and the reference's horizon-content height (tree tops read ~10° above the horizon
  → `(horizon_y − top_y)/f` rad). Reject maps whose horizon content sits metres from the HDRI
  camera (it fills the sky and leaves nothing bright for water/glass to reflect — an
  easy first pick). Rotation that puts equirect column u at world azimuth a (deg from +X):
  `ROT = 360·(0.5 − u) − a` (Mapping Z rotation, Cycles `u = 0.5 − atan2(y, x)/2π`).
- `archviz.hdri_analyse(id, rot)` integrates the upper hemisphere -> lux at strength 1 and the
  sun direction (luminance centroid of the top 0.05 % texels). `world_hdri_lux(id, target_lux)`
  scales it. Measure the HDRI rather than remembering it — every file differs, and the tool is
  one call.
- **Target illuminance** (these are the world, so they carry everywhere): full sun 80-100 klux,
  overcast daylight 10-20 klux, a bright north-lit studio ~2 klux, a tabletop studio ~500 lux.
- Equirect: `u = 0.5 - atan2(y,x)/2π`, `v = elev/π + 0.5`; world Mapping rotates the lookup (Rzᵀ).
- **The HDRI is the only natural light (RULES 8a).** No sun lamp with it, ever. Use its sun
  direction (`hdri_analyse`) to rotate the map so the sun falls where the shot needs it (the
  rotation formula above), and scale it with `world_hdri_lux`. `sun_from_direction` is only for
  scenes with no HDRI (a bare sun-only test or control).
- **Pick the HDRI by its sun when sun matters** (hard shadows, caustics, sunlit patches):
  measure the sun share — horizontal irradiance of the texels within ~1.5° of the sun centroid
  vs the whole upper hemisphere. A clear-sky map whose disc carries ~70–90 % is unclipped and
  gives crisp shadows and caustics; a map well under ~60 % (partly cloudy, hazy, clipped) gives
  soft shadows and washed caustics — choose another map rather than adding or boosting a sun.
  Check its sun elevation too: it cannot be changed, only the azimuth (by rotation).
- **What a window shows of the HDRI:** for a viewer at eye height h_e looking through glazing
  from z0 to z1, the horizon sits at (h_e − z0)/(z1 − z0) of the glass height (~45 % for a
  1.5 m eye and 0.4–2.9 m glass). Horizon content above 0° fills the upper glass; to keep trees
  in the lower third with open sky above (and a sun that plausibly shines in), the tree tops
  must sit at or below 0° — a viewpoint/hill HDRI, not a clearing ringed by trees. Profile
  candidate maps by elevation in a ±50° azimuth window around the sun (green vs blue, median
  luminance per 5°) instead of judging thumbnails. Horizon content, sun elevation and sun share
  all have to fit in one map, so shortlist widely.
- Sky Texture `MULTIPLE_SCATTERING` (5.2 name): calibrate with a white-plane render.

## Artificial light (formulas measured to 0.2 %, `scripts/controls/light_units.py`)
Convert from the lumens printed on the fixture — that is the number a lighting schedule gives you.

- **Spot/point = point-equivalent**: power is for the full sphere, the cone only masks.
  F lm into a full beam angle a: `P = F/683 · 4π / (2π(1 - cos a/2))` → `interior.downlight(lumens, beam_deg)`.
- **Area = Lambert emitter**: `E = P/(πd²)` on axis; `spread` focuses the same power.
  Strip: `P = lm_per_m · L / 683` → `interior.led_strip(p0, p1, lm_per_m, normal, spread)`.
  For a target E at distance d: `P = E·π·d²/683`.
- **Emissive lens**: `L = F/(πA)` cd/m², strength = L/683 → `interior.lens_luminance`.
- Colour: `light.use_temperature`, `light.temperature` (K). Warm white 2700-3000 K, neutral
  3500-4000 K, daylight 5000-6500 K.
- **Typical fixture outputs**, as starting points before the scene tells you otherwise: a domestic
  downlight is several hundred to ~1000 lm; an LED cove or niche strip runs a few hundred lm/m
  (grazing a wall wants the low end — a bright strip close to a surface blows the top out);
  a pool or feature light is ~1-2.5 klm. Set from the reference, not from this list.

## Placement and visibility
- Wall grazing: a thin area strip a few centimetres off the wall at the top, toed slightly in.
  Spots used as washers give scallops.
- Recessed fixture: `visible_camera = False` on the light (it sits in a slot).
- **Count each fixture once.** Either the lens is the source (luminance from lumens, visible to
  all rays) or the lens is decor for an analytic light → `interior.lit_once()` = `visible_diffuse`
  AND `visible_transmission` off. Visibility follows the LAST bounce: a diffuse ray through water
  arrives as *transmission*, so turning diffuse off alone still leaks (that is how a ceiling
  turned green).
- Underwater lights: aimed spots along the pool; a Lambert lens near the surface throws most of
  its light out onto the ceiling instead of into the water.

## Camera
- `physical_camera(cam, iso, f, shutter, focal)`: `EV100 = log2(N²/t) - log2(ISO/100)`,
  `exposure = log2(683/1.2) - EV100`; the same f-stop drives DOF.
- **Typical EV100 by condition** — the most portable numbers in this file, because they describe
  light, not a scene:

  | Condition | EV100 | A workable triple |
  |---|---|---|
  | Bright sun | 15 | ISO 100, f/11, 1/125 |
  | Overcast exterior | 12-13 | ISO 100, f/8, 1/60 |
  | Studio / product | 10-11 | ISO 100, f/8, 1/15 |
  | Daylit interior | 9 | ISO 200, f/5.6, 1/30 |
  | Dim night interior | ~5 | ISO 800, f/8, 1/4 |

  Archviz convention: a longish exposure on a tripod, so prefer a mid aperture for depth and
  move shutter/ISO. Pick the triple a photographer would actually use for that light.
- `straighten_verticals(cam)`: level + `shift_y = lens·tan(pitch)/sensor_width`.
- White balance: `view_settings.use_white_balance`, `white_balance_temperature` = the colour
  shown neutral — **lower = cooler**. Setting WB above the lamp temperature keeps warmth in the
  image rather than neutralising it, which is usually what a warm reference wants.

## Recreating a reference
### Camera
1. `refmatch.py grid ref.png out.png --step 25` -> read the horizon (where parallel horizontal
   edges converge) and the vanishing point of the dominant direction. Crop and zoom regions
   (Pillow) to read edges; one full-frame look misreads thin members.
2. Eye height without a known size: a vertical element standing on the floor splits at the
   horizon — `(top - horizon) / (horizon - base)` in pixels = `(H - eye) / eye`. Pick a plausible
   H (clear height, rail, door) and the eye follows; its width/height ratio then sizes it.
3. Focal: assume a common archviz lens, then check proportions in the overlay; parallel lines in
   one direction alone cannot fix the focal.
4. Level camera + lens shift (parallel verticals). **Shift trap:** with `sensor_fit = HORIZONTAL`,
   `shift_x/shift_y` are fractions of the frame **width** even on a portrait frame, and +shift_x
   moves the frame right, so the principal point appears left:
   `shift_x = -(vp_x - W/2)/W`, `shift_y = (horizon_y - H/2)/W` (pixels from the top).
   Verify by projecting a far point on the axis with `world_to_camera_view` — it must land on the
   measured vanishing point. Never trust the first framing render by eye.
5. **Conditioning of readings.** Depth from a floor point is `f·eye/(y − horizon)`: a point a
   few pixels below the horizon swings metres per pixel. Two floor lines read 2-3 px apart near
   the horizon disagreed by ~1 m in plan. Trust points far from the horizon — soffit
   edges high in the frame, floor points near the camera — and treat near-horizon readings as
   loose. When two readings disagree, ask which one is well conditioned before adding geometry.
6. Check the Rhino model before Blender: `scripts/rhino/project_edges.py` (in Rhino via Rook,
   with the solved camera) + `scripts/edge_overlay.py` draws its edges over the reference. Rook
   viewport captures ignore the requested size, so a lens-shifted named view captures wrong.
7. `archviz.framing_render()` + `refmatch.py pair --overlay`; move geometry, not the camera, once
   the vanishing point and one height match.

### Camera from a repeated element (colonnade, mullions, bays)
Code: `scripts/refsolve.py readings.json` (and `Solve.floor_pt / plane_pt / pt_at_z / fit_circle /
blender()` from a study script). Read the base and top of every repeat at full resolution (ticked
2x crops, not the downscaled frame). Then:
- Lines through the bases and through the tops meet at the façade vanishing point; its y is the
  horizon (level camera).
- Apparent height h ∝ 1/depth, so equal steps in 1/h prove an equal pitch, and the pitch (or one
  known size) fixes the scale. Eye height = H · (y_base - horizon)/h, the same for every repeat —
  which is your check on the readings.
- Focal is the weak unknown. The ellipse of a round base gives depression angle ≈
  asin(sagitta / half-width), so f ≈ (y_base - horizon)/tan(angle). Per-column values scatter
  widely, so take a plausible lens and judge by the overlay rather than averaging them.
- With f, eye and horizon fixed, image -> plan is two formulas. A floor point is at depth
  `Z = f·eye/(y - horizon)`, `X = (x - cx)·Z/f`. A point on a known vertical plane: intersect the
  pixel ray with that plane. Read wall bases, openings and lamps this way. The repeats falling on
  one straight line in plan means the solve holds.
- Keep the solve as a small script in the study: every later geometry question becomes one call.

### Geometry readings
- When a reading fits one cue but not the structure (a beam that "ends" at another beam's soffit,
  a member too thin to span), prefer the structurally plausible reading — a downstand beam runs to
  the slab — and fix the light instead. If still ambiguous, state the reading and let the user
  correct it.
- A deep element casting shade over a region that is bright in the reference means either the
  geometry or the light position is wrong: check both before adding light.
- **What stays visible decides the reading.** A dark band under a slab can read as a downstand
  when it is really a step *up* in the ceiling, with the band being the wall head inside the
  recess — and the downstand reading hides fixtures the reference clearly shows. Before keeping
  any member, check that it does not cover something visible in the reference.
- **Fit a curve where it meets its neighbour.** A free circle fit through floor points will push
  a drum out of place; constrain it to meet the wall plane at the pixel where it visibly emerges.
- Open vs roofed: a region bright in the reference but black in the render is usually roofed in
  the model — but cut the roof only where the reference shows open sky, or you light it from
  above and lose the shape.

### Light, region by region
1. `refmatch.py patches ref.png regions.json render.png` (regions.json in the study folder:
   `{"name": [x0, y0, x1, y1], …}` in 0..1, y from top; ~10 regions: each lit surface type, the
   shadow side, floor near/far, the background). Keep a table of render/ref ratios per iteration;
   aim for *equal* ratios first, then exposure.
2. Read where the light comes from before placing any:
   - **Visible fixtures may face away.** A lamp head seen from behind lights the far room, not
     the foreground.
   - **Cast shadows give direction.** Shadow width w thrown by a member of depth d onto the
     surface it hangs from -> source elevation ≈ atan(d / w), on the opposite side.
   - A region brighter than anything its visible sources can reach means an **out-of-frame
     source** (behind or beside the camera). Add it, check it is outside the frustum (project its
     position), and **declare it** — it is not in the reference image.
   - Check the ray from a candidate source to the target clears intervening members before
     trusting it (a beam can shadow the bay you are trying to light).
3. Spots and floods: a wide cone aimed at a ceiling also lights the column and walls in front of
   it. When one element is too bright, find which cone it sits in (angle from the axis) and narrow
   or re-aim *that* light rather than dimming everything.
4. Graded references (flat, sepia): AgX *Base Contrast*, white balance near the lamp temperature,
   and tone the material albedo warm/cool before touching grading. The look follows the reference,
   not habit — a crisp reference wants a contrastier look even if the last job didn't.
5. **Glass and what it shows.** Façade glass reflects only ~5-8 % at 30-50° incidence, so glazing
   that reads bright in the reference is lit *from behind*, not reflecting more. White sheers that
   read several times brighter than surrounding stone need real illuminance on their backs — a
   modest room wash will stay stubbornly dark. Model the backlight as a wash about a metre behind
   the sheer and **declare** it (rooms beyond, not in the image). For the reflection itself,
   mirror the camera ray in the glass normal, then pick the HDRI rotation from luminance by
   azimuth: trees on the horizon band, bright sky higher up for upper floors. Rotate the HDRI,
   not the glass.
6. Exposure last (RULES 7). When every region is off by the same ratio, *that* is the exposure
   step, so take it then.

## Misc
- Area lights emit along local -Z. With rotation (θ, 0, 0) the beam goes along (0, sin θ, -cos θ):
  -90° faces -Y, 145° points up and toward +Y. Print the world direction after creating the light.
- Pendant globes: a solid glass sphere is a lens ball. Give it a thin Solidify shell, IOR 1.5 and
  mid roughness so it reads as lit glass (`lookdev.glass_shell(objs)`). The bulb is a point light
  with `visible_camera = True`; hide the bulb mesh so the fixture counts once.
- Backdrop that lights nothing: Mix(HDRI, white Background, Light Path *Is Camera Ray*); under AgX
  display-white needs ~4/2^exposure.
- AgX rolls whites off: match targets on the written PNG, not on linear values.
