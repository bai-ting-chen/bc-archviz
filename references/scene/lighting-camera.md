# Lighting and camera — real units

One constant everywhere: **683 lm per Blender W** (lights, HDRI lux, camera exposure).

## Daylight
- **Matching an HDRI to a reference** (RULES LGT_02). Shortlist by tags from the Poly Haven API
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
- Placing the sun (RULES LGT_02): rotate the map by its `hdri_analyse` sun direction (formula
  above), scale with `world_hdri_lux`. `sun_from_direction` is for scenes with no HDRI (tests,
  controls).
- **Pick the HDRI by its sun when sun matters** (hard shadows, caustics, sunlit patches):
  measure the sun share — horizontal irradiance of the texels within ~1.5° of the sun centroid
  vs the whole upper hemisphere. A clear-sky map whose disc carries ~70–90 % is unclipped and
  gives crisp shadows and caustics; a map well under ~60 % (partly cloudy, hazy, clipped) gives
  soft shadows and washed caustics — choose another map. Check its sun elevation too: rotation
  changes only the azimuth.
- **What a window shows of the HDRI:** for a viewer at eye height h_e looking through glazing
  from z0 to z1, the horizon sits at (h_e − z0)/(z1 − z0) of the glass height. Horizon content
  above 0° fills the glass above that line; to keep landscape low with open sky above, it must
  sit at or below 0° (a map shot from a viewpoint, not from inside a clearing). Profile candidate
  maps by elevation in an azimuth window around the view direction (colour and median luminance
  per few degrees) instead of judging thumbnails. Horizon content, sun elevation and sun share
  all have to fit in one map, so shortlist widely.
- Sky Texture `MULTIPLE_SCATTERING` (5.2 name): calibrate with a white-plane render.

## Artificial light (formulas measured to 0.2 %, `scripts/controls/lighting/light_units.py`)
When the fixture is specified, use its IES file (*IES profiles* below) — it carries the beam and
the intensity. Otherwise convert from the lumens printed on the fixture — the number a lighting
schedule gives you.

- **Spot/point = point-equivalent**: power is for the full sphere, the cone only masks.
  F lm into a full beam angle a: `P = F/683 · 4π / (2π(1 - cos a/2))` → `interior.downlight(name, loc, lumens, beam_deg)`.
- **Area = Lambert emitter**: `E = P/(πd²)` on axis; `spread` (`spread_deg` in the helpers) focuses the same power.
  Strip: `P = lm_per_m · L / 683` → `interior.led_strip(name, p0, p1, lm_per_m, normal=…, spread_deg=…)`.
  For a target E at distance d: `P = E·π·d²/683`.
- **Emissive lens**: `L = F/(πA)` cd/m², strength = L/683 → `interior.lens_luminance`.
- Colour: `light.use_temperature`, `light.temperature` (K). Warm white 2700-3000 K, neutral
  3500-4000 K, daylight 5000-6500 K.
- **Typical fixture outputs**, as starting points before the scene tells you otherwise: a domestic
  downlight is several hundred to ~1000 lm; an LED cove or niche strip runs a few hundred lm/m
  (grazing a wall wants the low end — a bright strip close to a surface blows the top out);
  a pool or feature light is ~1-2.5 klm. Set from the reference, not from this list.

## Light types — which one models what
| Source | Use for | Units / traps |
|---|---|---|
| World (HDRI / Sky) | all daylight (RULES LGT_02) | lux via `world_hdri_lux` |
| Point | bulbs, **any IES fixture** | W for the full sphere; Radius = bulb/lens size (softness only) |
| Spot | downlights/spots without an IES | same power as a point, the cone only masks; Blend softens the edge, not the shadow |
| Area (rect/square/disk/ellipse) | panels, troffers, coves, light boxes, backlit sheers | Lambert emitter, P = flux; *Spread* narrows like a louvre/honeycomb; *Portal* in windows only samples the HDRI (no light of its own) |
| Sun | tests and controls only (RULES LGT_02) | W/m² |
| Emissive mesh | visible lenses, LED lines, screens, signage | luminance cd/m² (`interior.emitter`); count once with the analytic light (`lit_once`) |

Per-light Cycles settings: *Max Bounces*, *Cast Shadow*, *Multiple Importance* (keep on for
area lights and glossy floors), *Shadow Caustics* (MNEE, [caustics.md](../effects/caustics.md)); *Light Linking* limits
what a light reaches; the light tree (Sampling › Lights, on by default) is what keeps dozens of
fixtures from turning into noise. *Normalize* (default on) keeps power constant as the size
changes; *Exposure* multiplies by 2^x — keep both at defaults so watts stay lumens/683.

## IES profiles — measured fixtures (`interior.ies_light`, control `scripts/controls/lighting/ies_units.py`)
An IES file (ANSI/IES LM-63) is the goniophotometer test of one luminaire: candela on a grid of
vertical angles (0° = nadir) × horizontal C-planes, plus a multiplier, ballast factors and the
lamp lumens. It holds the beam shape, cut-off, side-throw and the absolute intensity, so with
the manufacturer's file a render's illuminance is the fixture's, not a guess from a cone angle.
- **Cycles' scale is 177.83 lm/W, not 683.** The IES node converts candela with 4π/177.83
  (D65 efficacy, `intern/cycles/util/ies.cpp`), applies multiplier × ballast factors, then
  multiplies by the light's power/4π. On a point/spot, power **177.83/683 = 0.2604 W** gives the
  file's candela in our convention (measured 0.999, real files 1.000). A 1 W light with an IES
  is 3.84× too bright — the usual "IES lights look blown out" complaint.
- **Host it on a point light** (or a spot with the cone opened to 180°). On an area light the
  profile multiplies a Lambert emitter: 4× on axis and cosine-weighted, no longer the
  measured distribution.
- **Orientation:** nadir = light −Z, C0 plane = light −Y, C90 = light −X. Asymmetric files (wall
  washers, asymmetric downlights) are aimed with this. LM-63 puts a luminaire's length on the
  90–270 axis, so a linear fixture's length goes on light −X.
- **Linear fixtures** (coves, linear pendants, wall-grazers): one point light with the file is
  right only far away (> ~5× the length). Split the run into N point lights along it, each with
  the same file at lumens/N — exact for a uniform emitter, because each piece has the whole
  fixture's angular shape at 1/N of its intensity. Keep each piece shorter than ~¼ of its
  distance to the lit surface.
- **Absolute vs relative photometry.** LED files are absolute (lamp lumens −1; candela are the
  fixture's). Older lamp files are relative: candela are for the rated lamp lumens and already
  include the luminaire efficiency, so the integrated flux (e.g. 852 lm) is below the lamp's
  (1650 lm). Either way the file is self-calibrated: use it unscaled. `ies_read` integrates the
  candela to the luminaire lumens, beam (50 %) and field (10 %) angles; it matched a file's own
  absolute-lumens tag to 0.3 %.
- **Rescale** only for a different lumen package or a dimmed scene: `ies_light(lumens=…)` keeps
  the shape and sets the flux. Colour temperature does not change luminance (measured).
- **Radius** of the host point light = the lens size: it softens shadows and highlights but the
  file assumes a point at far field, so the pattern near a wall (< ~5× the lens size) is
  approximate. **Keep the whole sphere clear of geometry:** the light is a sphere, and any part of
  it inside the ceiling or a housing is shadowed. A 45 mm sphere centred 3 mm under a ceiling
  delivered 0.57× its flux to the floor. Centre it radius + 2 mm below the surface.
- **Check a lit room by hand:** direct-only illuminance (every surface but a Lambert floor black;
  `max_bounces = 0` is not used for this) against Σ I(γ)·cos γ / r² from the files at a grid of
  floor points. Unshadowed points should agree within ~1 %; points that disagree reveal
  occluders or misplaced lights.
- **Files:** the manufacturer's product page (photometry / downloads tab) is the source of
  truth — match the exact catalogue number, lumen package, CCT and optic. Aggregators:
  ieslibrary.com (search by manufacturer; account + API key; previews CC BY-ND), Acuity brands
  bulk zips; the DIALux online catalogue (luminaires.dialux.com) has a direct *Photometric data*
  zip on each article page, no account. Some makers expose a plain file tree (the LM-79 report
  PDF's URL with `.ies` often serves the file). European makers often ship Eulumdat `.ldt`
  only: Cycles reads IES only, so convert with `scripts/scene/lighting/ldt2ies.py in.ldt out.ies` (MCP venv
  python), which prints the lumens integrated from the written file against the LDT's. Save into the study's `library/local/ies/` with a `meta.json` (maker, catalogue,
  URL, lumens) (RULES AST_03). `ies_light` embeds the file in the .blend (Internal mode).

## Placement and visibility
- Grazed or washed wall (when the design calls for it): a linear source along the wall — a thin
  area light or emissive slot. Offset and aim set the effect: closer and steeper means more
  texture relief and falloff; size them from the fixture or the reference. A row of spots on a
  wall gives scallops; use spots only when scallops are intended.
- Recessed fixture: `visible_camera = False` on the light (it sits in a slot).
- **Count each fixture once** (RULES LGT_01). Either the lens is the source (luminance from lumens, visible to
  all rays) or the lens is decor for an analytic light → `interior.lit_once()` = `visible_diffuse`
  AND `visible_transmission` off. Visibility follows the LAST bounce: a diffuse ray through water
  arrives as *transmission*, so turning diffuse off alone still leaks.
- Underwater lights: aimed spots along the pool; a Lambert lens near the surface throws most of
  its light out onto the ceiling instead of into the water.

## Camera
- `physical_camera(cam, iso, f, shutter, focal)`: `EV100 = log2(N²/t) - log2(ISO/100)`,
  `exposure = log2(683/1.2) - EV100`; the same f-stop drives DOF.
- **Typical EV100 by condition** — the most portable numbers in this file, because they describe
  light, not a scene:

  | Condition | EV100 | A workable triple |
  |---|---|---|
  | Bright sun | 15 | ISO 100, f/16, 1/125 |
  | Overcast exterior | 12-13 | ISO 100, f/8, 1/60 |
  | Studio / product | 10-11 | ISO 100, f/8, 1/15 |
  | Daylit interior | 9 | ISO 200, f/5.6, 1/30 |
  | Dim night interior | ~5 | ISO 800, f/8, 1/4 |

  **From the illuminance instead** (incident meter, C = 250): EV100 = log2(E_lux / 2.5); an
  interior at ~400 lux on the work plane wants EV100 ≈ 7. Read E off a Lambert patch in a
  linear render (lux = 683·π·pixel / albedo) rather than guessing the condition.
  Archviz convention: a longish exposure on a tripod, so prefer a mid aperture for depth and
  move shutter/ISO. Pick the triple a photographer would actually use for that light.
- `straighten_verticals(cam)`: level + `shift_y = lens·tan(pitch)/sensor_width`.
- White balance: `view_settings.use_white_balance`, `white_balance_temperature` = the colour
  shown neutral — **lower = cooler**. Setting WB above the lamp temperature keeps warmth in the
  image rather than neutralising it, which is usually what a warm reference wants.
- **Warming toward a reference:** move the temperature only; leave `white_balance_tint` at its
  daylight-neutral default 10. A tint pushed far off 10 so that one floor patch matches the
  photo's hue cast the whole frame pink. Check the hue of the whole frame (walls, background,
  glass), not one patch.

### Soft backplate, crisp model
An HDRI backplate (trees, hills) is soft - in its photo, not only its resolution: a
higher-resolution camera-ray window over the lighting map (same equirect lookup, registers
exactly) barely sharpens it. The modelled building then reads cut out. Measure edge
widths (10-90 % or step/max-gradient) on a model edge against the backplate and on a backplate
edge, then use a little depth of field: focus slightly in front of the subject (e.g. f/4 at
~0.6x the subject distance) so the model edge softens ~1.3x and the backplate a bit more. Keep
EV100 by the shutter.

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
   few pixels below the horizon swings metres per pixel. Trust points far from the horizon — soffit
   edges high in the frame, floor points near the camera — and treat near-horizon readings as
   loose. When two readings disagree, ask which one is well conditioned before adding geometry.
6. Check the Rhino model before Blender: `scripts/rhino/project_edges.py` (in Rhino via Rook,
   with the solved camera) + `scripts/research/edge_overlay.py` draws its edges over the reference. Rook
   viewport captures ignore the requested size, so a lens-shifted named view captures wrong.
7. `archviz.framing_render()` + `refmatch.py pair --overlay`; move geometry, not the camera, once
   the vanishing point and one height match.

### Camera from a repeated element (colonnade, mullions, bays)
Code: `scripts/research/refsolve.py readings.json` (and `Solve.floor_pt / plane_pt / pt_at_z / fit_circle /
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
6. Exposure last (RULES RES_03). When every region is off by the same ratio, *that* is the exposure
   step, so take it then.

## Fog and mist (`atmosphere.fog_volume`, control `scripts/controls/lighting/fog_koschmieder.py`)
- Fog/mist droplets 5-20 um: Mie scattering, strongly forward, no absorption (white). Volume
  Scatter, phase **Mie** (native in 5.2, Cycles) with the droplet diameter.
- Density = extinction coefficient sigma = 3.912 / V (Koschmieder, V = visibility, 2 %
  contrast). Control: absorption-only transmission through 29 m = exp(-sigma d) to 1.000.
  Dense fog V ~150 m: an object at 27 m keeps ~half its contrast, 80 m almost nothing.
- Shape: full below the fog top, smoothstep to clear air above it, denser in hollows, patchy
  noise (RULES MAT_05); a box around the site with the camera inside. Clear the inside of
  buildings (indoor air has no fog; a fog-filled dark room behind glass is also a noise source).
- Light: a sunless overcast HDRI (no sun lamp, RULES LGT_02). `atmosphere.volume_render_settings`:
  volume bounces (api-traps › Render). Cost ~2.5-3.5x a clear scene.
- Raw noise in the fog falls as 1/sqrt(N); OIDN cleans smooth fog without blotches at a few
  hundred spp - check a contrast-stretched sky crop.

## Misc
- Area-light direction: api-traps › Render (they emit along local −Z); print the world direction
  after creating the light.
- Pendant globes: a solid glass sphere is a lens ball. Give it a thin Solidify shell, IOR 1.5 and
  mid roughness so it reads as lit glass (`materials.glass.glass.glass_shell(objs)`). The bulb is a point light
  with `visible_camera = True`; hide the bulb mesh so the fixture counts once.
- Backdrop that lights nothing: Mix(HDRI, white Background, Light Path *Is Camera Ray*); under AgX
  display-white needs ~4/2^exposure.
- Match targets on the written PNG (RULES VAL_03).


## LGT_01 procedure

**Real units everywhere.** Daylight: calibrated HDRI in lux, nothing else (LGT_02). Artificial: lumens at
   683 lm/W — the same constant the camera uses, so a real ISO/f/shutter gives the right exposure
   without eyeballing. A specified fixture uses the manufacturer's photometric file (IES; LDT
   converted) at its catalogue output — never a power set by eye (lighting-camera › IES).
   Model each fixture once (a visible lens *and* an analytic light both lighting
   double the flux). White balance is a camera setting. Parallel verticals.


## LGT_02 procedure

**Natural light = matching HDRI sky first**. Whenever sun, sky or any
   daylight is in the scene, light it with an HDRI whose sky matches the reference (overcast vs
   clear, sun height and direction, horizon content) before any Sky Texture, sun-only rig or
   fake. Search Poly Haven by tag/thumbnail for the match; fall back to Sky Texture only when no
   HDRI fits, and say so. **The HDRI is the sole natural light source**:
   never a sun lamp alongside it — not "matched", not to boost a weak sun, not after painting the
   disc out. The HDRI's sun direction (`hdri_analyse`) only guides rotating and placing the map.
   If its sun is too weak or in the wrong place for the shot, choose another HDRI.
