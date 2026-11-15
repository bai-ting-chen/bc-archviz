# Attached water film

## 1. Overview
Water that clings to a surface as it runs down: a film on a wall, a stone face or glass.

**Use when:** the water stays on the surface. Water that leaves a lip and falls free:
[water-free-falling-film.md](water-free-falling-film.md). Both are the same film on a different
carrier, so this file holds only what differs and reuses the free-falling layers.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with attached-film settings.

```
                      ATTACHED WATER FILM — LAYER DIAGRAM
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                          GENERIC (own reference)            │
 │ §4.1 Surface carrier  → geometry       Streams, ribbons, meander, edges,  │
 │ §4.2 Film thickness   → depth            motion blur                      │
 │                                          → water-free-falling-film.md     │
 │                                        Water against glass → glass.md     │
 │                                        Wet surface around the film        │
 │                                          → wet-surfaces.md                │
 │                                        Entering the pool: ripples, foam   │
 │                                          → water-ripple/foam.md           │
 └───────────────────────────────────────────────────────────────────────────┘
   surface carrier (§4.1) ─► film coordinates (s along the surface, d down it)
   thickness (§4.2) × free-falling layers ─► film surface = carrier + thickness along the normal
   film surface ─► water material; on glass, the wetted face takes the interface IOR
```

- **One water body on the surface:** a single skin offset from the carrier; the wall or glass under it
  is the other face. Uneven thickness between the two faces is what bends the surface behind; a
  constant thickness is a parallel plate and bends nothing.
- **Same field layers as the free-falling film,** evaluated in the same (s, v) coordinates on the
  surface carrier instead of the ballistic one. Each stays its own term with its own switch (RULES MAT_07).
- **Size from the final view first** (RULES MAT_03): most rope and wave detail is sub-pixel at a
  building-scale view and reads only in aggregate (RULES MAT_04).

## 3. Code
No builder yet. The free-falling field layers in `scripts/blender/materials/water/film_fields.py`
(zones, swell, roll waves, meander, ribbons, tears) take only the film coordinates, not the carrier;
`film_surfaces.film_surfaces()` is the one place that evaluates them on the ballistic carrier. An
attached builder adds a surface carrier (§4.1) and calls the same field layers; it does not copy them (skill-maintaining.md › one builder per job).

## 4. Instructions and parameters, per layer
Table values are starting points; size them from the shot (RULES MAT_03) and record the final values
in the study notes (RULES GOV_01).

### 4.1 Surface carrier (geometry)
- **Check the section first.** A lip standing in front of the unit below (set-back) makes a strong
  flow leave the lip and fall free (free-falling film). A moderate flow wraps under a sharp lip
  (teapot effect) and rejoins the face below; a face leaning out a few degrees still holds a film.
  Measure the depth profile down one vertical line (raycast) before choosing.
- **Raycast the front-most surface** along −N on an (s, d) grid, finer across than down (streams run
  down). Low-pass the depth at the capillary scale, then add the thickness (§4.2), keeping the film
  clear of the surface so the two never touch.
- **The film follows broad relief and fills only the fine one.** A film of ~1 mm over folds much
  wider than itself keeps their full distortion: the film only splits the air → glass step (0.52) into
  air → water (0.33) and water → glass (0.19). It smooths only crinkle and creases at the capillary
  scale, so wet patterned glass is not generally clearer than dry.
- **Shared-row quads only,** so the sheet ends cleanly at each lip.

| Parameter | Value |
|---|---|
| Grid | ~3 mm across, ~6 mm down |
| Low-pass (capillary scale) | σ ≈ 5 mm |
| Clearance surface to film | ≥ 0.3 mm |

### 4.2 Film thickness (depth)
- **Mean thickness from the flow:** laminar (Nusselt) h = (3·ν·q / g)^(1/3), q = flow per metre width.
  It replaces the free-falling h = q/U.
- **Uneven, never constant:** at fountain flows (Re = q/ν ~ 10²–10³) the film is wavy. Thicker
  meandering streams (ropes) come from the free-falling stream flow and meander layers; roll waves
  from its ribbons layer, much weaker here.

| Parameter | Value |
|---|---|
| Mean thickness | ~0.5–1.5 mm |
| Rope thickness | several mm, λ 2–9 cm across |
| Roll waves | ~0.2 mm |

Generic layers, attached-film settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Stream flow q(y) | [water-free-falling-film.md](water-free-falling-film.md) §4.2 | ropes; q sets the Nusselt thickness, not the throw |
| Fall-time stretch | [water-free-falling-film.md](water-free-falling-film.md) §4.3 | k = 0: a film on a surface soon runs at a steady speed, so nothing stretches with the drop |
| Fine ribbons, calm zones, roll waves | [water-free-falling-film.md](water-free-falling-film.md) §4.4 | roll waves ~0.2 mm; judge at native resolution (RULES VAL_01) |
| Sideways meander | [water-free-falling-film.md](water-free-falling-film.md) §4.5 | ropes meander; no folding, the film stays on the surface |
| Tears | [water-free-falling-film.md](water-free-falling-film.md) §4.6 | same mask and rounded rims; dry patches and rivulets where the flow is low, not where the meander stretches |
| Dissolving edges | [water-free-falling-film.md](water-free-falling-film.md) §4.8 | side edges pull in to rivulets |
| Motion blur | [water-free-falling-film.md](water-free-falling-film.md) §4.9 | streak from the film's surface speed, far below a free fall |
| Water against glass | [glass.md](../glass/glass.md) §4.3 | the wetted glass face takes the interface IOR |
| Wet surface around the film | [wet-surfaces.md](../../effects/wet-surfaces.md) | splashed and damp margin beside and below the film |
| Ripples where the film enters the pool | [water-ripple.md](water-ripple.md) | the film runs in along the surface: ring waves and chop from its foot, no crater or crown |
| Foam, bubbles, aeration at the foot | [water-foam.md](water-foam.md) | parents along the foot of the film |

The ballistic carrier (§4.1 there) and strings and drops (§4.7 there) are not used.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Calm water bends nothing; film reads as clear glass | constant thickness: a parallel plate | uneven thickness from streams and ribbons (§2, §4.2) |
| Wet patterned glass looks clearer than dry | film smooths folds it should keep | follow broad relief, fill only the fine one (§4.1) |
| Film touches or cuts into the surface | no clearance | keep ≥ 0.3 mm between surface and film (§4.1) |
| Strong flow falls free in front of the units below | set-back lip | check the section; use the free-falling film (§4.1) |
| Squiggly contour-like highlights | fine relief and roll waves too strong | roll waves ~0.2 mm (§4.2) |

Streak, flute, comb and washboard problems of the shared layers: the free-falling film's §5.
Generic problems are in troubleshooting.md.
