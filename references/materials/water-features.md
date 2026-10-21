# Water features: films, cascades, overflows, whitewater, choppy pools

Stills of water running down a wall or glass, spilling into a trench or pool, and the pool around
it. Physics first (RULES RES_01), then how to build each part as geometry + shading in Cycles. Pool
water basics (absorption, ripples as geometry): [materials/water.md](water.md)

## Method: procedural or simulation?
| Approach | Use | Notes |
|---|---|---|
| Height fields / procedural geometry (numpy or GN) | stills; any film, sheet, pool surface | fast, sized to the shot, exact control; animate by a time input |
| Ocean modifier | open-water wind waves | cannot react to objects |
| Dynamic Paint *Waves* | ripples from objects touching water | stack after Ocean |
| Mantaflow (native FLIP) | splashes, plunges, fountains in motion | built in; has **spray / foam / bubble** secondary particles (domain › Particles); memory-hungry at high velocity |
| FLIP Fluids add-on | same, whitewater, sheeting, surface tension | verify the selected release/source edition: public v1.8.8 is Demo with mesh watermarks; full marketplace edition differs; see upstream README |
| GN simulation zones | no shipped fluid solver in 5.2 (cloth/hair XPBD only; fluid in progress) | community GN FLIP exists, slow |

- **A grid simulation cannot resolve a mm film on a wall of metres** (1 mm cells over 6 m is
  6 000 cells tall), and one-particle-thick layers are FLIP's known weak case. Films and sheets
  stay procedural.
- **Where simulation pays:** the plunge zone (splash, foam clumps, spray). Hybrid: simulate a
  short stretch (~1 m domain, 3–5 mm cells) with secondary particles, instance it along the line
  with random offsets/flips; keep film, crest and pool procedural.
- Houdini Apprentice is non-commercial and watermarked — not for client work.

### Thin-sheet inlets and hybrid boundaries
- Compute liquid thickness before choosing a domain: `delta = q / V`, q in m²/s per unit
  width, V normal to the cross-section in m/s. If delta is below one voxel, a fully occupied
  one-cell source cannot preserve both speed and discharge. A q-matched source slows to
  `V' = q / dx`; a speed-matched source over-discharges by `dx / delta`. State the momentum
  and energy deficit or flow excess; neither is a matched-physics benchmark.
- An oblique velocity also emits through side faces of a source box. For a rectangular prism
  spanning width w in X, velocity in YZ gives ideal projected discharge
  `Q = w * (abs(vz)*dy + abs(vy)*dz)`. Align its source extrusion axis with velocity while
  keeping width transverse to flow; use its normal cross-section when nominally matching q.
  Geometry × speed is not a measurement of
  the solver's injected volume; sample or instrument that separately when making a flux claim.
- Open domain sides drain a finite pool. Measure far-field level drift. A perimeter reserve
  held at the desired level approximates the surrounding pool; refilling the entire submerged
  domain also fills impact cavities and changes their dynamics. Record that boundary bias.
- A stitched simulation slice needs an actual pool opening. Extract the near-waterline
  boundary separately from the tall inlet curtain and detached spray before building an apron.
  Clip particles to the same per-slice footprint as their water surface; overlapping mirrored
  particle copies can make a false dense foam seam. Inspect joins in both wide and close views.
- Matching a nonlinear wave function at shared grid vertices is insufficient after refining
  just one side: intermediate points must interpolate the unchanged neighbor's boundary
  polyline, or both sides must be refined together. Check the saved meshes, not only formulas.
- Bake completion alone does not prove settled flow. Check stabilization over multiple frames,
  including a truncated bake that might already be steady. Keep failed pilots and costs explicit;
  promote a simulation hybrid only after a matched inlet and boundary comparison.

Sources: [upstream inflow requirements and emission settings](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Inflow-Object-Settings),
[domain grid and open boundaries](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Simulation-Settings),
[v1.8.8 Demo limitations](https://github.com/rlguy/Blender-FLIP-Fluids/tree/v1.8.8#readme).
The projected-area and delta formulas above are continuity geometry, not solver guarantees.

## Falling film on a wall or glass
- **Thickness:** laminar (Nusselt) h = (3·ν·q / g)^(1/3), q = flow per metre width. At fountain
  flows (Re = q/ν ~ 10²–10³) the film is wavy: roll waves (horizontal-ish crests, λ several cm)
  and rivulet **ropes** (thicker vertical streaks that meander). Mean ~0.5–1.5 mm, ropes several
  mm. The "volumetric" look of a good reference = wide glossy ropes refracting the wall behind
  into vertical streaks, plus trapped bubbles and aeration at the foot.
- **Build as a height field on the wall plane:** raycast the front-most surface along −N on a
  (u, z) grid (~3 mm across, ~6 mm down — ropes are vertical), per row/surface run: depth
  low-passed at the capillary scale + thickness, kept ≥ surface + 0.3 mm so the two never touch.
  Shared-row quads only, so the sheet ends cleanly at each lip.
- **The film follows broad relief, fills only the fine one.** A ~1 mm film over folds of λ ≫ film
  keeps their full distortion (air/water 0.33 + water/glass 0.19 ≈ dry glass 0.52); it smooths
  only crinkle and creases at the capillary scale (low-pass σ ≈ 5 mm). Wet patterned glass is
  *not* generally clearer than dry.
- **Glass under water in Cycles** (no nested IOR): the wetted glass face gets IOR 1.52/1.333 =
  1.14, the film surface 1.333 (as `glassware.glass_of_water`).
- **Check the section before choosing the flow.** Shingled or tilted units decide what water can
  do: a lip standing in front of the unit below (set-back) makes a strong flow leave the first lip
  and fall as one free sheet in front of everything below; a moderate flow wraps under a sharp
  lip (teapot effect) and rejoins the face below. A face leaning out a few degrees still holds a
  moving film. Measure the depth profile down one vertical line (raycast) before modelling.
- **Character traps:** fine relief + roll waves draw squiggly contour-like highlights; keep roll
  waves ~0.2 mm and ropes λ 2–9 cm. Judge at native resolution (RULES VAL_01).

## Free curtain off a lip: 2D ribbon pattern on a ballistic carrier
Once the flow detaches from the lip (check the section first — a low flow clings and wraps
under it, see *Falling film* › Check the section and *Overflow edge*), a thin curtain thrown off
the lip can be built without simulation: a carrier surface plus a 2D ribbon
field in the carrier's own (u, v), unioned into one watertight body (SDF).
- **Carrier = the trajectory (free-fall curtain).** Water leaves the lip horizontally, so the section is a parabola with
  its vertex at the lip: x(d) = v0·sqrt(2d/g), standoff growing monotonically with the drop d. Never a
  bulge that returns to the wall. Let v0 vary slowly and irregularly along the lip (q varies) so the
  landing line and the light gradient vary. Prove it with true sections against the analytic curve.
  - **Free fall:** after separation the only body force is gravity (projectile motion). This holds for the
    coherent sheet over a few metres. It fails where:
    - drops near the foot approach terminal speed (2 mm drop ≈ 6.5 m/s) while the sheet reaches √(2gH) ≈ 9 m/s at 4 m;
    - a curtain sealed to walls at both ends traps air behind it, the air is entrained, and the low pressure pulls the
      nappe toward the wall (weir ventilation). An open or torn curtain is aerated and stays ballistic.
  - **One family of profiles:** every section is the same one-parameter parabola z = −g·x²/(2·v0²). All sections share
    the separation line (the lip). The launch direction is the crest tangent at separation, horizontal off a sharp or
    flat lip. On a rounded crest the separation point slides round as v0 falls (cling, see *Overflow edge*).
  - **The surface is analytic, not lofted:** S(y, d) = (x_lip − v0(y)·√(2d/g), y, z_lip − d). Each section is exactly a
    parabola, and smoothness comes only from v0(y). Use a C¹/C² noise, two scales (metres + decimetres), never per-cell
    steps. A loft between drawn sections can wiggle or kink between them.
  - **Landing line** = the intersection with the receiving plane z_w: x_L(y) = v0(y)·√(2H/g), H = z_lip − z_w.
    The impact angle from horizontal is atan(√(2gH)/v0), near vertical (≈ 83° for 0.6 m/s off 4 m). Splash, foam and
    drops follow x_L(y) and vary along it.
  - **v0 is set by the flow:** off a free overfall v0 ≈ √(g·h_c), h_c = (q²/g)^(1/3), so v0 = (g·q)^(1/3) and the
    throw x_L ∝ q^(1/3). Doubling the throw takes ~8× the discharge per metre, or a projecting nozzle or lip. More q
    also means a thicker sheet that breaks up later. Declare it when a look asks for long throw *and* early breakup.
  - **Along the drop:** speed U = √(v0² + 2gd), and the sheet thins as h = q/U. Holes open, their rims retract
    (Taylor–Culick, V = √(2σ/(ρh))) and leave ligaments, which pinch into drops (Rayleigh–Plateau, drop ≈ 1.9 × ligament
    diameter). So gap fraction and gap size grow with d, string length falls, and the lowest band is fragments and
    drops. Measure the reference's coverage at top / mid / bottom and match that profile.
- **The carrier gives the volume.** A standoff of a few cm (often what a reference measures) reads
  as paint on the wall at a distance; size the standoff from the final view.
- **Ribbon traps (each seen in a failed round):**
  - ropes constant along their length = cylinders mirroring one band of the surroundings → chrome
    flutes. Ribbons must wander, swell, twist, braid and tear along their length;
  - correlation along the flow too short + dense spacing → etched/hammered glass;
  - a flat sheet of constant thickness is a parallel plate: no deflection (only a negligible
    sideways shift), ~4 % reflection at normal incidence from its two faces → invisible. Calm water needs uneven thickness *between its two faces* to
    bend the wall behind;
  - lenses placed one per grid cell → sprinkled dots; tears at a fixed pitch → slots; fields built
    only from sines and hashed cells read as a pattern;
  - stacking parallel thin layers adds bands, not volume.
- **Change one thing at a time.** Swapping the carrier must not retune the ribbon field; a look that
  works is kept byte-identical while the geometry under it changes.

## Overflow edge into a trench
- **Spill:** head h over a sharp crest → q ≈ 1.84·h^1.5 (m²/s); brink depth ≈ 0.715 × critical
  depth (2h/3); brink speed ≈ √(g·2h/3) — a few mm of head gives ~0.2 m/s, so the sheet **clings**
  round the edge and down the trench wall as a thin roped film.
- **Model the crest at the water line.** A slot drawn as a hole in the water surface, or a slot
  whose rim sits below the pond level, is a flooded channel, not an overflow. Ask which is meant.
- **Sight lines:** the visible depth into a gap = gap width × tan(camera depression angle). A low
  camera sees only the top centimetres of a narrow trench, so its white water must run high
  (tens of mm under the crest) and boil up in bursts to show — check this before tuning foam.
- A wide curb top under a few mm of water reads as a dark frame: knife edge (~10 mm), buried
  under the broken sheet and foam.
- One strip mesh round the rim (pond band with draw-down → roll over a rounded edge → film down
  the wall) parameterised by (perimeter s, distance d); square offset contours at the corners so
  it meets a rectangular hole in the far pond.

## Whitewater (plunge zones, trenches)
- **Optics:** a bubble cloud scatters σ_s ≈ 1.5·α / r (void fraction α, bubble radius r): 10 %,
  1 mm → 150 /m; 30 %, 0.5 mm → ~900 /m. Ten centimetres is optically thick — the floor of a
  churning trench never shows.
- **Render it as an opaque milky surface, not a volume.** A scattering volume in a shaded slot
  renders dark grey and slow. Use Burley subsurface (radius 3–4 cm) under a wet sheen (IOR 1.33,
  rough ~0.06), base around 0.35–0.45 albedo; foam (0.8, rougher, short radius) blended in as
  soft marbled streaks and lace; a few darker, less aerated streaks — never clear holes.
- **Never a hard foam switch.** Opaque white beside clear water over a dark trench reads as
  snow with black holes.
- **Rounded, not spiky.** Chop λ 4–15 cm, boils as domes (positive part^1.5) of 5–12 cm;
  short boils at large amplitude on a fine grid draw cones.
- **Fill below the surface.** An open water sheet over a void lets sight lines bent through
  adjacent glass end on the dark floor → a black band at the waterline. Put an opaque milky body
  just under the wave troughs.
- **Bursts, not a uniform band:** one along-line "scallop" field (bursts every 0.15–0.6 m)
  drives foam width, boil height and splash density together (cf. the scalloped impact line of
  large memorial waterfalls).
- **Splash:** drops from each plunge line, height exponential (mean 2–5 cm; max ≈ v²/2g ≈ 0.2 m
  at 2 m/s), elongated with speed, a share flung back over the crest; none left sitting in the
  surface. In soft light clear drops read **dark**, and dense low drops form a black band; drops
  sparkle only where they catch a bright reflection (sun or a bright sky direction).

## Choppy pool that hides the floor
- Geometry wavelets everywhere (λ 3–25 cm, steepness ~0.09), rougher within ~0.4 m of a plunge,
  under a slow gust envelope (0.3–1.6, λ 0.6–2.5 m) — 28 cosines read as a cross-hatch, use ~64.
- **One wave field object shared by every mesh touching the pond**, so near grid, crest band and
  far plane meet without seams; the far plane gets a hole matching the near region.
- At grazing view (~70°) water reflects only 6–10 %: the **floor sets the pool's tone**. Polished
  near-black stone (albedo 0.02–0.05) + absorption ~1.5 /m + chop removes the floor from view.

## Materials around water (sized for the final view, RULES MAT_03)
- **Brushed anodised metal:** Metallic BSDF F82 (edge tint brighter, warmer than base),
  anisotropy ~0.75 with the tangent from a directional UV along the part's length, brush streaks
  in roughness (noise stretched ~400:1); bevel 1–2 mm with hardened normals. Water marks as
  coffee rings (rim stronger), tide lines of dried puddles on tops, drip/tea streaks on verticals,
  AO dust in joints, ±6 % per-part tone. Spots under ~3 px vanish: at ~3 mm/px they need 8–25 mm.
- **Cast glass relief:** multi-scale (soft folds λ 8–40 cm + ridged creases + very weak
  crinkle), each tile its own cast, faded flat over ~30 mm at the border so the grid meets the
  untouched body; strong fine crinkle reads as squiggles. A slight roughness (~0.05) on the dry
  faces gives the satin haze of cast glass.
