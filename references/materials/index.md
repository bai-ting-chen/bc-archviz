# Materials

Recipes describe node structure and mechanisms; tune scene values in study notes (GOV_01).
Use all applicable maps at real size with physical surface ranges (MAT_01).

## Layer assembly (MAT_07)
- **Colour and roughness:** each layer is a multiplier around 1 on the base, chained in sequence.
  Older helpers that mix whole BSDFs or MAXIMUM masks (`edge_wear.weathered_concrete`,
  `add_runoff`) predate MAT_07: migrate them when they are next changed.
- **Height:** geometry-scale relief goes to the Displacement output ([displacement.md](displacement.md)),
  surface texture to a Bump node on the Normal input.
- **Switching off (MAT_07):** a Value node per layer that scales its deviation from 1 does it; an
  AOV of the layer's multiplier lets you measure what reaches the image ([variation.md](variation.md)).
- **Geometry fields** measured in Geometry Nodes run before modifiers that move the mesh (RULES MAT_08).

| Family or technique | Canonical helper |
|---|---|
| [Physical Ranges](physical-ranges.md) | `materials.pbr` |
| [Texture Selection](texture-selection.md) | `materials.pbr` |
| [Concrete](concrete.md) | `materials.concrete` |
| [Tiles](tiles.md) | `materials.tile_surface` |
| [Board Formed Concrete](board-formed-concrete.md) | `materials.concrete` |
| [Ground](ground.md) | `materials.ground` |
| [Vegetation](vegetation.md) | `materials.vegetation` |
| [Wet Surfaces](wet-surfaces.md) | `materials.vegetation` |
| [Displacement](displacement.md) | `materials.displacement` |
| [Wood](wood.md) | `materials.wood` |
| [Stone](stone.md) | `materials.stone` |
| [Metal](metal.md) | `materials.metal` |
| [Glass](glass.md) | `materials.glass` |
| [Caustics](caustics.md) | `gn_caustics` / `caustic_photons.py` |
| [Fabric](fabric.md) | `materials.fabric` |
| [Water Surface](water-surface.md) | `materials.water` |
| [Variation](variation.md) | `materials.variation` |
| [Scale](scale.md) | `materials.nodes` |
| [Edge Wear](edge-wear.md) | `materials.edge_wear` |
| [Water Free-Falling Film](water-free-falling-film.md) | `water.build.falling_film` (`water.curtain`, `water.film`, `water.fragments`) |
| [Water Attached Film](water-attached-film.md) | none yet (raycast height field) |
| [Water Ripple](water-ripple.md) | `water.ripple`, `water.pool` |
| [Water Foam](water-foam.md) | `water.foot` (foam, bubbles) |
| [Water Splash](water-splash.md) | `water.foot` (impacts, crowns, splash) |

Shared graph/socket helpers: `materials.nodes.G` / `sock`; asset lookup and project state: `archviz`.
Lighting stays in `interior`; geometry stays in `terrain` and `scatter`.
[LuxCore materials](../renderer/luxcore.md): `materials.luxcore`; [all helper signatures](../scene/blender-python-helpers.md).

## Water: which method, which file
Water comes in three build methods. Choose by the shot, then read the file for the kind of water.

| Method | Use | Cost / limits |
|---|---|---|
| **Surface** (shader + diced geometry, Ocean) | pools and still water | fast; reacts to nothing |
| **Field map** (2D fields in the water's own coordinates on an analytic carrier, numpy or GN) | stills of films, curtains, cascades and their foot | fast, sized to the shot, exact control; a physics-informed approximation, not a simulation |
| **Simulation** (Mantaflow, FLIP Fluids) | final-production accuracy, motion, splashes and plunges | slow, memory-hungry; a grid cannot resolve a mm film on a wall of metres (1 mm cells over 6 m = 6 000 cells); one-particle-thick sheets are FLIP's weak case |

- A field map follows physics for shapes, proportions and how they change along the flow; it skips
  conservation proofs and solver-grade validation. When a study asks for exact water, propose the
  simulation workflow as a separate job rather than pushing a field map toward it.
- Simulation tools: Ocean (open-water wind waves, cannot react to objects); Dynamic Paint *Waves*
  (ripples from objects touching water, stack after Ocean); Mantaflow (built-in FLIP with spray,
  foam and bubble particles); FLIP Fluids add-on (check the edition); no shipped GN fluid solver in
  5.2. Hybrid plunge zones: [water-splash.md](water-splash.md) › Simulated plunge zone.

| Water | File |
|---|---|
| Pool, still water, wind ripples | [water-surface.md](water-surface.md) |
| Sheet thrown off a lip, falling free | [water-free-falling-film.md](water-free-falling-film.md) |
| Film clinging to a wall or glass; low overflow into a trench | [water-attached-film.md](water-attached-film.md) |
| Ripples and waves from impacts; choppy plunge pools | [water-ripple.md](water-ripple.md) |
| Foam, floating bubbles, whitewater | [water-foam.md](water-foam.md) |
| Landing line, crowns, splash; simulated plunge zones | [water-splash.md](water-splash.md) |
| Wet surfaces around or behind water | [wet-surfaces.md](wet-surfaces.md) |
