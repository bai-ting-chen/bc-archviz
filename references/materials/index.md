# Materials
Use when: choosing which material or effect file (and helper) to read for a surface, or which water method to build.

Recipes describe node structure and mechanisms; tune scene values in study notes (GOV_01). Use all applicable maps at real size with physical surface ranges (MAT_01).

## Layer assembly (MAT_07)
- **Colour and roughness:** each layer is a multiplier around 1 on the base, chained in sequence.
   Older helpers that mix whole BSDFs or MAXIMUM masks (`edge_wear.weathered_concrete`,
   `add_runoff`) predate MAT_07: migrate them when they are next changed.
- **Height:** geometry-scale relief goes to the Displacement output ([displacement.md](displacement/displacement.md)),
   surface texture to a Bump node on the Normal input.
- **Switching off (MAT_07):** a Value node per layer that scales its deviation from 1 does it; an
   AOV of the layer's multiplier lets you measure what reaches the image ([variation.md](../effects/variation.md)).
- **Geometry fields** measured in Geometry Nodes run before modifiers that move the mesh (RULES MAT_08).

## Which file
**General rules and techniques** (this folder's root) apply to every material. **Materials:** pick the family the surface
is made of; effects used only by that family live with it (water ripple, foam, splash in `water/`). **Effects**
(`../effects/`) are layers shared by many materials. No row fits: the general rules still apply; a method the skill does not have yet goes through the research loop (RULES RES_01). Say which file and helper you chose and why (RULES MAT_09).

| General rules and techniques | Canonical helper |
|---|---|
| [Physical Ranges](physical-ranges.md) | `materials.shared.pbr` |
| [Texture Selection](texture-selection.md) | `materials.shared.pbr` |
| [Scale](scale.md) | `materials.shared.nodes` |
| [Displacement](displacement/displacement.md) | `materials.displacement.displacement` |

| Materials | Canonical helper |
|---|---|
| [Concrete](concrete/concrete.md) | `materials.concrete.concrete` |
| [Board Formed Concrete](concrete/board-formed-concrete.md) | `materials.concrete.concrete` |
| [Tiles](tile/tiles.md) | `materials.tile.tile_surface` |
| [Stone](stone/stone.md) | `materials.stone.stone` |
| [Wood](wood/wood.md) | `materials.wood.wood` |
| [Metal](metal/metal.md) | `materials.metal.metal` |
| [Glass](glass/glass.md) | `materials.glass.glass` |
| [Fabric](fabric/fabric.md) | `materials.fabric.fabric` |
| [Ground](ground/ground.md) | `materials.ground.ground` |
| [Vegetation](vegetation/vegetation.md) | `materials.vegetation.vegetation` |
| Water: [Surface](water/water-surface.md) | `materials.water.water` |
| Water: [Free-Falling Film](water/water-free-falling-film.md) | `materials.water.build.falling_film` (`materials.water.curtain`, `materials.water.film`, `materials.water.fragments`) |
| Water: [Attached Film](water/water-attached-film.md) | none yet (raycast height field) |
| Water: [Ripple](water/water-ripple.md) | `materials.water.ripple`, `materials.water.shading` |
| Water: [Foam](water/water-foam.md) | `materials.water.foot` (foam, bubbles) |
| Water: [Splash](water/water-splash.md) | `materials.water.foot` (impacts, crowns, splash) |

| Effects (shared) | Canonical helper |
|---|---|
| [Edge Wear](../effects/edge-wear.md) | `effects.edge_wear` |
| [Variation](../effects/variation.md) | `effects.variation` |
| [Wet Surfaces](../effects/wet-surfaces.md) | `materials.vegetation.vegetation`, `materials.water.wet` |
| [Caustics](../effects/caustics.md) | `gn_caustics` / `caustic_photons.py` |

Shared graph/socket helpers: `materials.shared.nodes.G` / `sock`; asset lookup and project state: `archviz`. Lighting stays in `interior`; geometry stays in `terrain` and `scatter`.
[LuxCore materials](../renderer/luxcore.md): `renderer.luxcore.luxcore`; [all helper signatures](../scene/blender-python-helpers.md).

## Water: which method, which file
Water comes in three build methods: choose the method by the shot, then the file by the kind of water. No row fits: a new method is needed (RULES RES_01). Say which method and file you chose and why (RULES MAT_09).

| Method | Choose when | Cost / limits |
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
  5.2. Hybrid plunge zones: [water-splash.md](water/water-splash.md) › Simulated plunge zone.

| Water (kind) | File |
|---|---|
| Pool, still water, wind ripples | [water-surface.md](water/water-surface.md) |
| Sheet thrown off a lip, falling free | [water-free-falling-film.md](water/water-free-falling-film.md) |
| Film clinging to a wall or glass; low overflow into a trench | [water-attached-film.md](water/water-attached-film.md) |
| Ripples and waves from impacts; choppy plunge pools | [water-ripple.md](water/water-ripple.md) |
| Foam, floating bubbles, whitewater | [water-foam.md](water/water-foam.md) |
| Landing line, crowns, splash; simulated plunge zones | [water-splash.md](water/water-splash.md) |
| Wet surfaces around or behind water | [wet-surfaces.md](../effects/wet-surfaces.md) |
