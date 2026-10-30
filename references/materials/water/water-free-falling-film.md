# Free-falling water film

## 1. Overview
A thin sheet of water thrown off a lip (a weir edge, a wall-top channel) and falling free in front
of the wall to a pool. Near the lip it is a glassy sheet; as it falls it speeds up, thins,
stretches, meanders sideways, tears into braids, and the lowest band breaks into strings and drops.
For a still, build it as a **2D field map in the sheet's own coordinates on an analytic carrier
surface**: a fast, physics-informed approximation, not a simulation (method choice:
materials/index.md › Water).

**Use when:** water leaves a lip and falls free to a pool. Water that clings to the wall instead:
water-attached-film.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with falling-film settings.

```
                           FREE-FALLING WATER FILM
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                          GENERIC (own reference)            │
 │ 1 Ballistic carrier   → geometry       Impact rings, waves, chop          │
 │ 2 Stream flow q(y)    → throw, depth                 → water-ripple.md    │
 │ 3 Fall-time stretch   → field coords   Foam, floating bubbles             │
 │ 4 Fine ribbons        → relief                       → water-foam.md      │
 │ 5 Sideways meander    → geometry       Crowns, splash, landing line       │
 │ 6 Tears and braids    → mask + rims                  → water-splash.md    │
 │ 7 Strings and drops   → geometry       Wet wall behind the water          │
 │ 8 Dissolving edges    → mask                         → wet-surfaces.md    │
 │ 9 Motion blur         → velocity attr  Pool body     → water-surface.md   │
 └───────────────────────────────────────────────────────────────────────────┘
   sheet coordinates (y along the lip, d drop)   what it drives
   carrier S(y,d) (1) ◄── v0(y) from q(y) (2)    surface position and normal
   v_eff(y,d) (3) ──► ribbons (4), meander phase (5), tear/strings fields (6, 7)
   thickness h=q/U × ribbons ─► front/back skins = carrier ± h/2 along the normal
   meander (5) ─► lateral shift of both skins ─► stretch field ─► tears (6)
   tears (6) + edges (8) ─► thickness → 0 at a rounded rim ─► faces removed inside
   strings, drops (7) ─► own meshes, from torn cells     velocity (9) on all three
```

- **One water body:** front and back skins of one closed mesh (a 2.5 mm grid over (y, d) is
  enough for the final view); strings and drops are separate meshes with the same water
  material. No stacked parallel layers (they add bands, not volume).
- **Each layer its own term** (RULES MAT_07): each scales a deviation and can be switched off for a
  control. Change one layer at a time; a look that works stays byte-identical while another
  layer changes.
- **Size from the final view first** (RULES MAT_03): compute mm per pixel on the curtain (vertical
  and along the wall, which is foreshortened). At a typical courtyard view one pixel covers
  ~4 mm × 10 mm, so drops, strings and roll-wave arcs are sub-pixel and read only in aggregate
  (RULES MAT_04). A close-up reference shows detail that cannot exist at that scale.

## 3. Code
`scripts/blender/materials/water/`: `build.falling_film(lip, pool_z, film_mat, …)` builds every layer in
§2 from a `curtain.Lip` (any straight lip: origin, along, out, length, drop) and returns objects and
stats. Parameters live in `build.Setup` (`curtain.Flow`, `film.FilmParams`, `fragments.FragmentParams`,
`foot.FootParams`, `ripple.RippleParams`, `wet.WetParams`). Modules: `mesh` (geometry), `motion`
(velocity), `shading` (materials, ripple bump). Defaults = the starting values in §4. `s_range` builds a
strip of the lip for a lab.

Control on an unrelated scene: `scripts/controls/water/falling_film_check.py`.

## 4. Instructions and parameters, per layer
Table values are starting points that held at one courtyard-scale view (~4 × 10 mm per pixel);
size them from the shot (RULES MAT_03), judge in a strip lab (validation.md), and record the final
values in the study notes (RULES GOV_01).

### 4.1 Ballistic carrier (geometry)
- Water leaves the lip horizontally, so each section is a parabola with its vertex at the lip:
  x(d) = v0·√(2d/g), standoff growing monotonically with the drop d. Never a bulge that
  returns to the wall.
- **Free fall holds** for the coherent sheet over a few metres. It fails where drops near the foot
  approach terminal speed (2 mm drop ≈ 6.5 m/s while the sheet reaches √(2gH) ≈ 9 m/s at 4 m), and
  where a curtain sealed at both ends traps air that is entrained and pulls the nappe toward the wall
  (weir ventilation). An open or torn curtain is aerated and stays ballistic.
- **Analytic, not lofted:** S(y, d) = (x_lip − v0(y)·√(2d/g), y, z_lip − d). Smoothness comes
  only from v0(y): C¹/C² noise at two scales (metres + decimetres), never per-cell steps. A loft
  between drawn sections can wiggle or kink. Prove it with true sections against the analytic
  curve.
- **v0 is set by the flow:** off a free overfall v0 ≈ √(g·h_c), h_c = (q²/g)^(1/3), so
  v0 = (g·q)^(1/3) and the throw x_L ∝ q^(1/3). Doubling the throw takes ~8× the discharge;
  declare it when a look asks for a long throw *and* early breakup.
- **Landing line** x_L(y) = v0(y)·√(2H/g); impact angle atan(√(2gH)/v0), near vertical.
- **Along the drop:** speed U = √(v0² + 2gd), thickness h = q/U.
- **Check the section first:** a low flow clings and wraps under a sharp lip (teapot effect) →
  water-attached-film.md.

| Parameter | Value |
|---|---|
| Throw at the foot (4 m drop) | a few cm reads as paint on the wall; ~0.2–0.35 m reads as a curtain — size from the view |
| v0 variation along the lip | ±40 %, two smooth scales |

### 4.2 Stream flow q(y) (throw and depth)
- **One flat profile is the tell:** every column on the same curve, at the same thickness, reads
  as a textured pane. Real lips deliver uneven flow: each stream carries its own q, so it has its
  own throw and thickness and stands at its own depth.
- q(y) = q̄(y)·(1 + m(y)), m a clustered, irregular, soft field; constant along each falling
  column. Per column: v0 = (g·q)^(1/3), h = q/U; thick streams get a rounded lens section, thin
  webs stay continuous between them.

| Parameter | Value |
|---|---|
| Stream widths | 40–250 mm, irregular, never periodic |
| Flow variation m | about ±40 % (±70 % reads heavier) |
| Max stream thickness | ~15–20 mm |

### 4.3 Fall-time stretch (field coordinates)
- A falling sheet stretches along the flow by U(d)/U(d₀): features born near the lip become long
  and gentle lower down. Evaluate every along-fall pattern in an effective coordinate
  v_eff(d) = ∫ (U(d_ref)/U(s))^k ds, keeping the top band unchanged below d_ref.
- k = 1 is the physical stretch; lower k stretches less. Render two values side by side and let the
  look decide.
- Without it, ridges and valleys flip at one fixed rate from lip to foot (a rigid rhythm).

| Parameter | Value |
|---|---|
| k | start at 0.5 (1 = physical) |
| d_ref (unchanged top band) | ~0.15 m |

### 4.4 Fine ribbons (relief)
- A 2D ribbon field in (y, v_eff): ribbons that wander, swell (varicose), twist flat ↔ round,
  braid, and tear; nothing constant along its length, nothing periodic.
- **Keep it gentle:** slope p99 ~0.3 rad at full strength. Steeper fine relief (p99 ~0.9 rad)
  becomes a uniform busy texture, a bright comb at the crest, and swamps every broader layer.
  Cut too far (to ~15 %) and the film turns to clear glass.
- **Calm and busy zones:** scale the relief by a clustered field in [0.4, 1], patches 0.3–1 m,
  stretched with v_eff, loosely correlated with q (thick streams busier).
- **Small roll-wave arcs** across the flow (two irregular trains, ~3.5 and ~8 cm, each crest its
  own strength and extent, on/off heights per stream, growing with the drop) at ~0.6 mm. At the
  final view they are nearly sub-pixel: stronger, they read as ladders or chevrons.
- A broad sinuous/varicose swell (80–200 mm, a few mm) is invisible under the fine relief; it
  only shows once the relief is gentle.

| Parameter | Value |
|---|---|
| Fine relief strength | measured as slope: p99 ≲ 0.3 rad at full zone strength |
| Calm/busy zone range | 0.4–1, patches 0.3–1 m |
| Roll-wave arcs | ~0.6 mm, λ ~3.5 and ~8 cm, ±35–45 % irregular, growing ~1×/m of drop |

### 4.5 Sideways meander (geometry)
- **At the final view the film reads as wavy vertical streaks.** Straight streaks read as ruled
  glass; the missing ingredient is a sideways meander of the water itself.
- Two along-fall scales (~3–10 cm and ~8–25 cm in v_eff), phases that change across the wall over
  a few cm, amplitude growing with the drop: Δy = A·w(y, v_eff)·(0.4 + 0.3·d).
- **The fold trade-off:** a meander that varies over a few cm across the wall folds a continuous
  sheet (Δy′ < −1). A fold-free version (neighbours in step over 10–30 cm) reads as a washboard and
  rows of bright dots. Use the independent meander, and **tear the sheet where it is stretched**
  (§4.6): the remaining folds are water pushed together = braids crossing. Measure the folded
  fraction of water quads (Δy′ ≤ −1 where both sides are water) and render-check the folds at the
  final view; if they show as dark blotches or crumpling, lower the amplitude or tear more of the
  stretched sheet.

| Parameter | Value |
|---|---|
| Meander amplitude A | ~14 mm (×0.4–1.7 down the fall) |
| Folded water quads | measure and report; acceptable only if the final view shows no artifacts |

### 4.6 Tears and braids (mask + rims)
- **Where:** a sheet pulled apart thins and tears; pushed together it piles into braids. Tear where
  the meander's stretch 1 + ∂Δy/∂y exceeds a threshold, plus narrow slits from a field that is
  narrow across (1–3.5 cm) and long along the stretched fall. Tearing starts part-way down and
  steepens toward the foot.
- **Shape:** thickness → 0 over a rounded rim (√ profile) with the swept volume as a slight bead
  on the edge; faces fully inside a tear are removed, so front and back skins meet at the seam.
- **Never round holes:** a hole born low is young and stays round (Taylor–Culick opening with no
  time to stretch); a hole born high grows wider than the gaps a reference shows. Physical hole
  models with narrow-gap limits give round dots. Tears follow the meander and the stretch instead.
- **Coverage is a look decision, not a fitted number:** keep the film mostly whole through the
  middle, break up toward the foot.

| Parameter | Value |
|---|---|
| Tear start | ~40 % down the drop, threshold falling as (d − d₀)^1.4 |
| Stretch threshold | 1 + ∂Δy/∂y > 2.2 |
| Slit width | 1–3.5 cm |
| Rim bead | ~2 mm |
| Torn fraction | ~10–15 % overall, ~40–45 % in the bottom rows |

### 4.7 Strings and drops (geometry)
- **A gap is never empty.** Where the sheet tears, the gap holds hanging strings and falling drops;
  a hard edge between water and empty reads false even when coverage is right.
- **Gap fill** (densities per m² of torn area, so they scale with the curtain): strings follow the
  local water path, beaded (varicose) along their length, slightly in front of or behind the
  sheet; drops elongated along the fall.
- **Edge drops and ligaments** shed at torn edges, more lower down; ~30 % are short stretched
  ligaments rather than drops. Drop ≈ 1.9 × ligament diameter (Rayleigh–Plateau).
- At the final view they are sub-pixel: they add sparkle and fill, not visible beads.

| Parameter | Value |
|---|---|
| Gap strings | ~900 per m² of torn area; radius 0.7–1.8 mm; length 2–40 cm (median ~9 cm); ±12 mm in depth |
| Gap drops | ~5 000 per m² of torn area; 1.2–7 mm |
| Edge drops | ~570 per m of curtain, weighted by drop; 2.5–8 mm; 30 % ligaments (stretch 4–9×) |

### 4.8 Dissolving edges (mask)
- A free edge is pulled inward by surface tension as it falls and breaks into strings and drops;
  a clean straight edge is a rigid tell.
- The edge line retreats with the drop and wavers; a band beside it tears much more, feeding the
  same strings and drops. Near the lip the edge stays crisp.

| Parameter | Value |
|---|---|
| Retreat | ~6 cm·d^1.3 at the foot, wavering ±1.5 cm |
| Dissolve band | ~20 cm, extra tearing from ~0.6 m down |

### 4.9 Motion blur (velocity attribute)
- Very slight blur keeps the water transparent and volumetric yet in motion. The mesh does not
  move: give film, strings and drops a `velocity` POINT FLOAT_VECTOR attribute = U(d) along the
  local fall direction (strings, drops straight down), and enable deformation motion blur on those
  objects only. Foam, bubbles and splash stay sharp.
- Units and shutter: blender-api-traps › Render. Streak at the foot = U_foot × shutter time;
  size it in pixels at the final view.
- Motion blur stores extra vertex steps: check VRAM on a heavy film before the final (RULES SAF_02).

| Parameter | Value |
|---|---|
| Streak at the foot | ~1–2 px (≈1/1200 s at 9 m/s and ~4 mm/px); ~5 px already reads too blurry |

### 4.10 Generic layers, falling-film settings
| Layer | Reference | Falling-film note |
|---|---|---|
| Impact rings, waves, chop | [water-ripple.md](water-ripple.md) | sources = the film's own landing row, weighted by thickness |
| Foam, floating bubbles | [water-foam.md](water-foam.md) | clustered at impacts, drifting past both ends of the fall |
| Crowns, splash, landing line | [water-splash.md](water-splash.md) | landing line from §4.1 and the bottom row of §4.6 |
| Wet wall behind the water | [wet-surfaces.md](../../effects/wet-surfaces.md) › Wet wall behind falling water | the wall behind the whole footprint, not the film's distance |
| Pool body | [water-surface.md](water-surface.md) | clear pool, absorption, Ocean |

## 5. Troubleshooting
Generic problems are in troubleshooting.md. These are specific to this film:

| Symptom | Cause | Fix |
|---|---|---|
| Chrome flutes | ropes constant along their length mirror one band of the surroundings | ribbons that wander, swell, twist, tear (§4.4) |
| Etched / hammered glass | dense short-correlated relief | fall-time stretch, calm zones, gentler relief (§4.3, §4.4) |
| Reads as paint on the wall | standoff of a few cm | size the throw from the view (§4.1) |
| One flat textured pane | one carrier curve and thickness for every column | stream flow q(y) (§4.2) |
| Clear glass pane, lower film | fine relief cut too far | relief ~0.4, waves growing with the drop (§4.4) |
| Bright comb at the crest, uniform glitter | fine relief too steep everywhere | slope p99 ≲ 0.3 rad, calm zones (§4.4) |
| Ladder rungs / V chevrons | roll-wave arcs at one wavelength, aligned, too strong | two irregular trains, per-crest strength, ~0.6 mm (§4.4) |
| Horizontal band of activity | on/off term that depends on height only | per-stream on/off heights (§4.4) |
| Ruled vertical lines | streams fixed in y | meander (§4.5) |
| Washboard, rows of dots | meander too coherent across the wall | independent meander + tear where stretched (§4.5, §4.6) |
| Crumpled, dark blotches | meander folds a continuous sheet everywhere | tear the stretched parts; measure folded fraction (§4.5) |
| Triangle / wedge gaps | constant-rate hole opening on constant speed | tears along the meander and stretch, not hole wedges (§4.6) |
| Round holes | young holes from a physical hole model with narrow-gap limits | no hole field; slits along the flow (§4.6) |
| Hard divide water / empty at the foot | empty gaps | gap fill strings and drops (§4.7) |
| Edge too perfect | no edge retreat or breakup | dissolving edges (§4.8) |
| Looks frozen | no motion | velocity motion blur, 1–2 px (§4.9) |
| Silky, loses transparency | shutter too long | shorter shutter (§4.9) |
| Coarse, hard gap map | block cells, binary mask | contour-level fields, rounded rims (§4.6) |

Generic problems that often show up with this film, in troubleshooting.md:
- Splash drops read as a dark band;
- Foam reads as snow cones with black holes.
