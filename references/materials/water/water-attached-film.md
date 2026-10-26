# Attached water film (walls, glass, overflow edges)

## 1. Overview
Water that clings: a film running down a wall or glass, and a low overflow that wraps round a crest
and down a trench wall. Physics first (RULES RES_01), then geometry + shading in Cycles. Water that
leaves the lip and falls free is covered by [water-free-falling-film.md](water-free-falling-film.md).
Where the film lands: [water-splash.md](water-splash.md), [water-ripple.md](water-ripple.md),
[water-foam.md](water-foam.md).

**Use when:** water clings to a wall, a sheet of glass or an overflow edge. Water that leaves a lip
and falls free: [water-free-falling-film.md](water-free-falling-film.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with attached-film settings.

```
                           ATTACHED WATER FILM
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                            │
 │   §4.1 Film height field on the wall    → geometry, ropes, roll waves    │
 │   §4.2 Glass and film IOR               → shading (transmission)         │
 │   §4.3 Overflow rim strip               → geometry, clinging film        │
 │ GENERIC (own reference)                                                  │
 │   Landing: crowns, splash               → water-splash.md                │
 │   Landing: ripples                      → water-ripple.md                │
 │   Foam, bubbles, whitewater             → water-foam.md                  │
 └──────────────────────────────────────────────────────────────────────────┘
```

Flow:
```
   wall surface ──► raycast front-most surface along −N, (u, z) grid ──► depth, low-passed (§4.1)
   depth + thickness (§4.1) ──► film surface, kept ≥ wall + 0.3 mm
   wetted glass face (§4.2) and film surface ──► transmission IOR
   rim strip (§4.3): pond band → roll over the crest → film down the wall
   film lands ──► generic layers (splash, ripples, foam)
```

- The film follows broad relief and fills only the fine one (§4.1 sets the scale).
- Shared-row quads only, so the sheet ends cleanly at each lip.
- A flat sheet of constant thickness is a parallel plate; calm water needs uneven thickness between
  its two faces to bend the wall behind (§4.1).

## 3. Code
No builder or control script yet: index.md › Water lists the attached film as "none yet"
(raycast height field). The glass-under-water IOR (§4.2) is `glass_of_water()` in
`scripts/blender/materials/glass/glass_assembly.py`.

## 4. Instructions and parameters, per layer
Table values are starting points; size them from the shot (RULES MAT_03) and record the final values
in the study notes (RULES GOV_01).

### 4.1 Film height field on the wall (geometry)
- **Check the section before choosing the flow.** Shingled or tilted units decide what water can
  do: a lip standing in front of the unit below (set-back) makes a strong flow leave the first lip
  and fall as one free sheet in front of everything below
  ([water-free-falling-film.md](water-free-falling-film.md)); a moderate flow wraps under a sharp
  lip (teapot effect) and rejoins the face below. A face leaning out a few degrees still holds a
  moving film. Measure the depth profile down one vertical line (raycast) before modelling.
- **Thickness:** laminar (Nusselt) h = (3·ν·q / g)^(1/3), q = flow per metre width. At fountain
  flows (Re = q/ν ~ 10²–10³) the film is wavy: roll waves (horizontal-ish crests, λ several cm)
  and rivulet **ropes** (thicker vertical streaks that meander). The "volumetric" look of a good
  reference = wide glossy ropes refracting the wall behind into vertical streaks, plus trapped bubbles
  and aeration at the foot.
- **Build as a height field on the wall plane:** raycast the front-most surface along −N on a
  (u, z) grid (ropes are vertical), per row/surface run: depth low-passed at the capillary scale plus
  thickness, kept ≥ surface + 0.3 mm so the two never touch.
- **The film follows broad relief, fills only the fine one.** A ~1 mm film over folds of λ ≫ film
  keeps their full distortion (air/water 0.33 + water/glass 0.19 ≈ dry glass 0.52); it smooths only
  crinkle and creases at the capillary scale. Wet patterned glass is *not* generally clearer than dry.
- **Character traps:** fine relief + roll waves draw squiggly contour-like highlights. Judge at
  native resolution (RULES VAL_01).

| Parameter | Value |
|---|---|
| Mean thickness | ~0.5–1.5 mm (Nusselt, §4.1 thickness bullet) |
| Ropes | several mm thick, λ 2–9 cm |
| Roll waves | ~0.2 mm |
| Height-field grid | ~3 mm across, ~6 mm down |
| Low-pass (capillary scale) | σ ≈ 5 mm |
| Clearance wall to film | ≥ 0.3 mm |

### 4.2 Glass and film IOR (shading)
- **Glass under water in Cycles** (no nested IOR): the wetted glass face gets IOR 1.52/1.333 = 1.14,
  the film surface 1.333 (as `glass_of_water`, §3).

| Parameter | Value |
|---|---|
| Wetted glass face IOR | 1.14 (1.52 / 1.333) |
| Film surface IOR | 1.333 |

### 4.3 Overflow edge and rim strip (geometry)
- **Spill:** head h over a sharp crest → q ≈ 1.84·h^1.5 (m²/s); brink depth ≈ 0.715 × critical
  depth (2h/3); brink speed ≈ √(g·2h/3) — a few mm of head gives ~0.2 m/s, so the sheet **clings**
  round the edge and down the trench wall as a thin roped film.
- **Model the crest at the water line.** A slot drawn as a hole in the water surface, or a slot
  whose rim sits below the pond level, is a flooded channel, not an overflow. Ask which is meant.
- **Sight lines:** the visible depth into a gap = gap width × tan(camera depression angle). A low
  camera sees only the top centimetres of a narrow trench, so its white water must run high
  (tens of mm under the crest) and boil up in bursts to show — check this before tuning foam.
- **Rim strip:** one strip mesh round the rim (pond band with draw-down → roll over a rounded edge →
  film down the wall) parameterised by (perimeter s, distance d); square offset contours at the
  corners so it meets a rectangular hole in the far pond.

| Parameter | Value |
|---|---|
| Spill rate | q ≈ 1.84·h^1.5 (m²/s) |
| Brink depth | ≈ 0.715 × critical depth (2h/3) |
| Brink speed | ≈ √(g·2h/3); a few mm of head ≈ 0.2 m/s |
| Curb knife edge | ~10 mm (a wide curb top under a few mm of water reads as a dark frame) |
| Visible depth into a gap | gap width × tan(camera depression angle) |

Generic layers, attached-film settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Landing: crowns, splash | [water-splash.md](water-splash.md) | where the film lands |
| Landing: ripples | [water-ripple.md](water-ripple.md) | where the film lands |
| Foam, bubbles, whitewater in the trench | [water-foam.md](water-foam.md) › Whitewater | the trench white water; the sight-line rule in §4.3 comes first |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Calm water bends nothing; film reads as clear glass | flat sheet of constant thickness: a parallel plate | uneven thickness between the two faces (§4.1) |
| Squiggly contour-like highlights | fine relief + roll waves too strong | roll waves ~0.2 mm, ropes λ 2–9 cm (§4.1) |
| Wet patterned glass looks clearer than dry | film smooths folds it should keep | film follows broad relief, fills only the fine one (§4.1) |
| Strong flow falls free in front of the units below | set-back lip | free-falling film file: [water-free-falling-film.md](water-free-falling-film.md) |
| Moderate flow wraps under a sharp lip and rejoins the face below | teapot effect | check the section before choosing the flow (§4.1) |
| Dark frame round a trench | wide curb top under a few mm of water | knife edge ~10 mm (§4.3) |
| Slot reads as a flooded channel | crest drawn as a hole, or rim below the pond level | model the crest at the water line (§4.3) |
| Trench white water does not show | low camera sees only the top centimetres | white water tens of mm under the crest, boiling in bursts (§4.3) |

Generic problems: `references/workflow/troubleshooting.md` (not linked from this file: a link here
would close a reference loop).
