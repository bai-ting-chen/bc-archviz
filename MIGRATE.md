# MIGRATE — run before anything else, then delete

## 261016 — Water features: films, overflow edges, whitewater, choppy pools
Pull-only. New `references/water-features.md`: method choice (procedural vs Mantaflow / FLIP
Fluids, and why mm films cannot be simulated), falling films on walls and textured glass
(Nusselt thickness, ropes, which relief a film fills), overflow crests (spill, clinging sheet,
sight-line depth into a trench), whitewater as an opaque milky surface (bubble-cloud optics,
soft foam, fill under the surface, splash drops), choppy pools that hide the floor, and brushed
metal / cast glass beside water sized for the final view. Pointers added in SKILL.md
(references table, 4 troubleshooting rows), materials.md (Water, Metal), capabilities.md;
pipeline.md: matching a Rhino named view's FOV; api-traps.md: Vector Rotate AXIS_ANGLE, Burley
subsurface on open sheets. No code changed.

### 1. Read the new reference
Check: this machine's session has read `references/water-features.md` (or the user says so).
Do: read it before the next water study; nothing to install.

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
