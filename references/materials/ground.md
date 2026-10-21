# Ground

- Exposed-aggregate precast (columns, slab edges): box-map an aggregate map at real size. Use the
  same map on fascia and soffit bands, and put soffits (Normal Z < -0.5) on a smoother, darker
  concrete via a second material slot.

## Terrain (landform grading)
`terrain.landform_group(centre=…, pad_half=…, fall=…, run=…)` + `terrain.add_terrain(group, ground)`.
- A building on a hill: flat pad just under the slab, an apron, then the fall as a smoothstep in
  the distance from the pad - a rounded crest **and** a rounded toe (landform grading, natural
  slopes), never a cone or a linear batter. Warp the distance with a slow noise so contours
  wander; add a broad roll beyond and pasture hummocks (+-5-10 cm at ~1.5 m).
- Steepest slope of a smoothstep fall = 1.5 x fall / run. Gentle / mowable: <= 4:1 (25 %);
  3:1 is the usual limit for maintained grass.
- To read as a hill, the camera stands down the slope with the crest against the sky; the
  edge of the generated grid must stay out of frame (the frustum mask hides the rest).
- `terrain.height(x, y, ...)` is the no-noise twin for placing a camera at eye height.
