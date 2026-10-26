# Attached water film (walls, glass, overflow edges)

Water that clings: a film running down a wall or glass, and a low overflow that wraps round a crest
and down a trench wall. Physics first (RULES RES_01), then geometry + shading in Cycles. Water that
leaves the lip and falls free: [water-free-falling-film.md](water-free-falling-film.md). Where it
lands: [water-splash.md](water-splash.md), [water-ripple.md](water-ripple.md), [water-foam.md](water-foam.md).

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
  and fall as one free sheet in front of everything below
  ([water-free-falling-film.md](water-free-falling-film.md)); a moderate flow wraps under a sharp
  lip (teapot effect) and rejoins the face below. A face leaning out a few degrees still holds a
  moving film. Measure the depth profile down one vertical line (raycast) before modelling.
- **Character traps:** fine relief + roll waves draw squiggly contour-like highlights; keep roll
  waves ~0.2 mm and ropes λ 2–9 cm. Judge at native resolution (RULES VAL_01).
- **A flat sheet of constant thickness is a parallel plate:** no deflection (only a negligible
  sideways shift), ~4 % reflection at normal incidence from its two faces → invisible. Calm water
  needs uneven thickness between its two faces to bend the wall behind.

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
- Whitewater in the trench: [water-foam.md](water-foam.md) › Whitewater.
