# Board-formed concrete

## 1. What it is
Concrete poured into moulds built from timber boards. The hardened surface is a negative cast of
the formwork: each board's face, its tilt and offset, the joints between boards, and the wood grain.
Treat it as **relief plus a faint print**, wherever boards are large enough in frame to resolve. A
printed board map is only a fallback for distant or small walls (§3.6).

## 2. Layers and how they combine
Specific layers are described here. Generic layers are written once, in their own reference, and
used here with board-form settings.

```
                          BOARD-FORMED CONCRETE
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§3)                         GENERIC (own reference)             │
 │ 1 Base concrete      → colour, rough  Chips at joints   → edge-wear.md    │
 │ 2 Board layout/tilt  → geometry       Dirty joints/edge → edge-wear.md    │
 │ 3 Joint marks        → displacement   Run-off, leaks    → edge-wear.md    │
 │ 4 Grain per board    → bump + ink     Concave dust      → variation.md    │
 │ 5 Board tone         → colour         Per-unit variety  → variation.md    │
 │                                       Wet / dew         → wet-surfaces.md │
 └───────────────────────────────────────────────────────────────────────────┘
   order of evaluation          node-editor output it drives
   GN: boards as cells (2) ───────────────────────────► mesh (welded, manifold)
   joints (3) + chips ────────► Displacement output ──► true displacement
                                (along the board normal; displacement.md)
   grain (4) ─────────────────► Bump ──► Normal ──────► Principled Normal
   base (1) × board tone (5) × grain ink (4) × grime/run-off/leaks
                                ─► Base Color ──► wet mix ──► Principled
   base roughness ± grime ± wet ─────────────────────────────────────────► Roughness
```

Assembly follows RULES MAT_07 (layers) and MAT_08 (geometry fields); displacement setup is in
[displacement.md](../displacement/displacement.md).
- **Joints displace, faces bump:** everything at a board joint (fins, grooves, steps, arrises,
  chips) is true displacement; everything on a board face (grain) is bump only. Faces stay cheap;
  joints keep their silhouette and shadow line.

## 3. Instructions and parameters, per layer

### 3.1 Base concrete
- A clean, jointless concrete or plaster with no board marks: [concrete.md](concrete.md),
  surface ranges in [physical-ranges.md](../physical-ranges.md) (RULES MAT_01).
- **Tone target:** match the reference's typical wall, not its brightest patch.

| Parameter | Value |
|---|---|
| Display value of a typical lit wall | below ~0.8 |

### 3.2 Board layout, tilt and offset (geometry)
- Courses, butt joints, board widths from the formwork drawing or reference.
- **Boards are never coplanar.** Each tilts about its long axis and sits slightly in or out, so
  courses step at the joints and catch light differently. This is what reads at a distance.
- Size it as the **edge excursion** (tilt + offset), not a tilt angle: an angle grows with board width.
- **Build:** boards as GN cells, welded and manifold.

| Parameter | Value |
|---|---|
| Edge excursion per board | ±1–3 mm |

### 3.3 Joint marks (displacement)
- Paste leaks between boards make **light, ragged fins** a few mm proud, broken in places.
- Where fines are lost, the joint band is **rougher and darker**.
- **The joint is the deepest feature on the wall:** a groove along each joint between two boards
  (not round wall tops, ends or feet), clearly deeper than the grain, and wide enough to be
  resolved by the dicing at the final view.
- **Combine, never add:** fin, groove and chips are combined with MIN/MAX and capped, so one
  cannot cancel another (a summed groove erased the fin) or exceed the cap.
- **Clamp every distance** that drives a fin or a displacement.
- **Chips:** mostly the thin paste fin breaking off in short ragged lengths, plus small shallow
  losses at the arris — no deep bites. Method and fresh-break colour: [edge-wear.md](../../effects/edge-wear.md)
  (RULES MAT_02), sized from the shot (RULES MAT_03). On meshes already subdivided wall-wide, build
  the chip field as displacement through the adaptive dicing (edge-wear.md › Chips as displacement).

| Parameter | Value |
|---|---|
| Fin height | a few mm proud |
| Fin continuity | broken in places, never a continuous bead (RULES MAT_05) |
| Groove depth | ≥ 2 × the grain depth |
| Groove width at the surface | ≥ 2 px at the final view |
| Chip reach / depth | ~5–10 mm / ~2–3 mm |

### 3.4 Grain inside each board (bump + ink)
- **Relief:** ridges of hard latewood (raised on the board by weathering or sandblasting) cast as
  **grooves** in the concrete: the dark figure of the grain map is recessed. Prove the sign on a
  test plane with a raking light before the scene (one dark stripe must read as a groove).
- **Relief alone is too faint at room scale.** Add a print, as colour multipliers (RULES MAT_07):
  - **ink 1:** density field × grain map, calibrated to a small mean darkening;
  - **ink 2 (optional):** the darkest figure only, near-black, in its own patches, so some areas
    read crisp and others faded.
- **Grain strength varies across the wall:** one low-frequency field scales both the bump depth and
  the ink. Driving the ink alone changes nothing visible: the bump shading dominates.
- **Edges dissolve, never blur:** jitter the height threshold with fine noise, warp the lookup
  slightly, and add a fine grit only in the rim band. Blur flattens the grain.

**Grain source.** Plank scans' displacement maps hold board bow, gaps and wear, but almost no
grain. The grain lives in their diffuse and normal maps, and weathered hardwood scans carry little
figure even there. Extract a grain map from a strongly figured diffuse, natively in a Compositor
graph:
- luminance → Blur (light denoise) → Blur (high pass at a few latewood spacings) → Subtract;
- local contrast normalisation (divide by a blurred local deviation, radius about one plank width);
- Map Range for levels; File Output, 16-bit;
- no directional smoothing (it rounds off curved latewood and knots);
- sample per board from plank interiors only.

**Continuity rule.** Grain is continuous within a board and never continuous across a joint. No two
formwork boards are alike, so neighbours differ (RULES MAT_06):
- give each board its own window of the grain source: offset over the whole usable map, flip in u
  and v, about ±0.5° angle, about ±10 % scale; choose windows whose grain runs along the board;
- crop windows with a Mapping node per board (origin and size as attributes), not by cutting pixels;
- no two adjacent boards may share a window that lines up: same course, the course above and below,
  and across corners.

| Parameter | Value |
|---|---|
| Grain depth (physical) | ~0.2–1 mm; a few mm only when the wall is read from far away |
| Ink 1 mean darkening | ~8 % |
| Ink 2 coverage / darkening | ~30 % of the wall / ~0.4 |
| Strength field | ×0.3–1.5, patches 0.3–1.5 m, stretched along the boards |
| Window angle / scale jitter | ±0.5° / ±10 % |
| Neighbour check | grain correlation across each joint (2 cm strips) below a threshold |

**Proof:** a raking-light patch beside the reference before any final-view render. Then check the
final view's mm per pixel: relief finer than a pixel reads only through its tone (RULES MAT_04).

### 3.5 Board tone (colour)
- Soft per-board tone from absorbency: a per-unit key, from [variation.md](../../effects/variation.md) (RULES MAT_06).
- Small, and never stepping harder than the joints themselves.

### 3.6 Printed board map (fallback for distant walls)
- Most board-formed maps run horizontal. To stand them up, feed a FLAT projection with
  Combine(z, along-wall):
  - planar walls: x + y;
  - a cylinder: arc length `atan2(y − cy, x − cx) · R`, which also avoids box-projection stretch.
- Vary tone per formwork strip (white noise on `floor(along / strip width)`) × a low-frequency field.
  That reads as cast panels and hides the tile repeat.
- → `materials.concrete.concrete.vertical_boards(mat, cylinder=(cx, cy, r) | None)`.

### 3.7 Generic layers, board-form settings
| Layer | Reference | Board-form note |
|---|---|---|
| Chips | [edge-wear.md](../../effects/edge-wear.md) | at board arrises, as displacement (§3.3) |
| Dirty joints / edge grime | [edge-wear.md](../../effects/edge-wear.md) | joint band rougher and darker (§3.3) |
| Run-off streaks | [edge-wear.md](../../effects/edge-wear.md) › Runoff | from each wall's own top; vertical faces only |
| Joint leaks | [edge-wear.md](../../effects/edge-wear.md) › Runoff | short drips under the horizontal joints, a pattern per joint, ending at the next joint |
| Concave dust | [variation.md](../../effects/variation.md) (RULES MAT_06) | at inside corners and wall feet |
| Wet / dew | [wet-surfaces.md](../../effects/wet-surfaces.md) | darkens and smooths all layers above |

## 4. Troubleshooting (board-formed specific)
Generic problems are in [troubleshooting.md](../../workflow/troubleshooting.md). These are specific to this material:

| Symptom | Cause | Fix |
|---|---|---|
| Wall reads as cladding, not concrete | tilt sized as an angle; edge excursion far over ±3 mm | size the edge excursion (§3.2) |
| Neighbouring boards show the same grain lined up | too few variants (a few source bands × a flip) | more windows over the whole map, all jitters, neighbour check (§3.4) |
| Grain invisible at the final view | relief only, too faint | add the ink print (§3.4) |
| Grain looks the same everywhere | strength field drives only the ink | let it drive the bump depth too (§3.4) |
| Grain reads raised, not recessed | bump sign | test plane with a raking light; invert the height (§3.4) |
| Grain softened, knots rounded | directional smoothing or blur | isotropic high-pass; dissolve edges with noise (§3.4) |
| Grain confused with the joints | joints as shallow as the grain | joint groove ≥ 2 × the grain depth (§3.3) |
| Joint fin missing beside the groove | depths summed | combine with MIN/MAX (§3.3) |
| Printed map runs the wrong way or stretches on a curved wall | wrong projection | FLAT projection with Combine(z, along-wall) (§3.6) |

Generic problems that often show up on this material, in [troubleshooting.md](../../workflow/troubleshooting.md):
- Relief vanishes on a bright wall;
- Displacement shelf from a negative distance;
- Chips read as dark spots;
- Grunge invisible, or reads as smoke;
- Scan-based grunge brings bands or lines;
- Visible joint grid on walls / a curved wall (tile repeat);
- Printed map stains repeat.
