# Board Formed Concrete

### Board-formed concrete
Concrete poured into moulds built from timber boards, so the surface is board-marked: it keeps
the imprint of each board's face and wood grain.

**Three independent layers, in this order:**
1. **Base:** a clean, jointless concrete (or plaster) material with no board marks.
2. **Board layer:** the board layout and joints.
   - **Layout:** courses, butt joints, board-to-board tone.
   - **Tilt and offset:** each board's own tilt and in/out offset.
   - **Joint marks:** paste fins and paste loss at the joints.
3. **Grain layer:** wood grain from a timber/wood material, placed *inside each board*.

**Grain continuity rule:** grain is continuous within a board and never continuous across a joint.
- **Why:** no two formwork boards are alike, so neighbours differ.
- **How:** give each board its own window of the grain source (offset over the whole usable map,
  flip in u and v, about ±0.5° angle, about ±10 % scale).
- **Neighbours:** no two adjacent boards may share a window that lines up. That covers the same
  course, the course above and below, and boards across corners.
- **Check:** correlate the grain height across every butt and bed joint in 2 cm strips; each pair
  must stay below a threshold.
- **Trap:** a few source bands × a flip gives too few variants, and neighbours line up.

Relief, not a print: the wall is a negative cast of the board faces, at three scales, all from
the formwork. Use this wherever boards are close or large enough to resolve; a printed board map
(below) is only a fallback for walls far away or small in frame.
- **Boards are never coplanar:** each board tilts about its long axis and sits slightly in or out,
  so courses step at the joints and each catches the light differently — this is what reads at a
  distance. Size it as the *edge excursion* (tilt + offset), about ±1–3 mm; a tilt angle alone
  misleads (2° about the centreline of a 280 mm board moves each edge ~5 mm, 10 mm edge to edge,
  and reads as cladding).
- **Joints:** paste leaks between boards → light ragged fins a few mm proud, broken in places;
  where fines are lost the joint band is rougher and darker. Joints are the strongest marks.
- **Grain is very faint beside the joints:** ~0.2–1 mm, strength varying per board, ridges from
  hard latewood (raised by weathering/sandblasting) cast as grooves. Never put grain in the albedo;
  board tone comes only from absorbency (soft, per board) and from the relief itself.
- **Grain source:** plank scans' displacement maps hold board bow, gaps and wear but almost no
  grain — it lives in their diffuse/normal maps, and weathered hardwood scans carry little figure
  even there. Bake one 16-bit map = the plank's own displacement + a grain map from a strongly
  figured softwood diffuse (isotropic high-pass at a few latewood spacings, sized from the scan;
  local contrast normalisation; ridge enhancement; no directional smoothing — it rounds off curved latewood and knots), latewood proud
  on the board, cast negative, sampled per board from plank interiors only.
- **Tone target:** match the reference's typical wall, not its brightest patch. Near display ~0.8,
  AgX's highlight roll-off flattens the relief shading and the grain, steps and fins all vanish.
- **Build:** boards as GN cells (welded, manifold); clamp every distance that drives a fin or
  displacement — one negative joint distance amplified a fin ~100× into a shelf on the floor.
  Prove the grain in a raking-light patch beside the reference before any final-view render, then
  check the final view's mm-per-pixel: relief finer than a pixel reads only through its tone.
- **Printed board maps (fallback for distant walls).** Most board-formed maps run horizontal. To
  stand them up, feed a FLAT projection with Combine(z, along-wall): x+y on planar walls, and on a cylinder
  the arc length (atan2(y-cy, x-cx)·R), which also avoids box-projection stretch on the curve.
  Then vary tone per formwork strip (white noise on floor(along / strip width)) x a low-frequency
  field — that reads as cast panels and hides the tile repeat. If the map's stains repeat
  visibly, mix the diffuse part-way toward its own mean.
  → `materials.concrete.vertical_boards(mat, cylinder=(cx, cy, r) | None)`.
