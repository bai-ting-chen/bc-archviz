# IES profiles

## 1. Overview
Fixtures lit from the manufacturer's photometric file (IES, or Eulumdat LDT converted), which
carries the beam shape and the absolute intensity.

**Use when:** the fixture is specified. Without a file, use `artificial-light.md`.

## 2. Layers and node-editor diagram
```
 ┌─ IES PROFILES — PROCEDURE DIAGRAM ──────────────────────────────────────┐
 │ File          manufacturer's .ies (convert .ldt) ─► study library      │
 │   ▼                                                                    │
 │ Read          lumens, beam and field angles                            │
 │   ▼                                                                    │
 │ Host          point light at 177.83/683 W ─► IES Texture ─► Strength   │
 │   ▼                                                                    │
 │ Aim           nadir −Z, C0 −Y, length −X                               │
 │   ▼                                                                    │
 │ Linear runs   N point lights at lumens/N                               │
 │   ▼                                                                    │
 │ Check         direct illuminance against the file                      │
 └────────────────────────────────────────────────────────────────────────┘
```

## 3. Code
- `scripts/blender/scene/lighting/artificial.py` (module `scene.lighting.artificial`):
  - `ies_light(name, path, location_m, rotation_rad, lumens, kelvin, radius, kind)`: the light, with
    the file embedded in the .blend.
  - `ies_read(path)`: lumens, beam (50 %) and field (10 %) angles integrated from the candela.
- `scripts/scene/lighting/ldt_to_ies.py in.ldt out.ies` (MCP venv python): converts Eulumdat and prints
  the lumens of the written file against the LDT's.
- Control: `scripts/controls/lighting/ies_units.py`.

## 4. Instructions and parameters
1. **File.** The manufacturer's product page is the source of truth: match the catalogue number,
   lumen package, CCT and optic. Aggregators: ieslibrary.com (account), luminaires.dialux.com
   (direct *Photometric data* zip per article). Save it in the study's `library/local/ies/` with a
   `meta.json` (maker, catalogue, URL, lumens) (RULES AST_01). Cycles reads IES only: convert LDT.
2. **Read.** `ies_read`. LED files are absolute (lamp lumens −1); older lamp files are relative and
   already include the luminaire efficiency. Either way the file is self-calibrated: use it unscaled.
3. **Host.** `ies_light` on a point light (or a spot with the cone opened to 180°). Cycles converts
   candela at 177.83 lm/W, not 683, so the host power is 177.83/683 = 0.2604 W; a 1 W light with an
   IES is 3.84× too bright. On an area light the profile multiplies a Lambert emitter and is no
   longer the measured distribution. Rescale with `lumens=` only for another lumen package or a
   dimmed scene.
4. **Aim.** Nadir = light −Z, C0 plane = light −Y, C90 = light −X. LM-63 puts a luminaire's length on
   the 90–270 axis, so a linear fixture's length goes on light −X.
5. **Linear runs** (coves, linear pendants, grazers). One light with the file is right only beyond
   ~5× the fixture length. Split the run into N point lights, each with the same file at lumens/N,
   each piece shorter than ~¼ of its distance to the lit surface.
6. **Check.** Direct-only illuminance on a Lambert floor (other surfaces black) against
   Σ I(γ)·cos γ / r² from the files at a grid of points. Unshadowed points agree within ~1 %; points
   that disagree reveal occluders or misplaced lights.

| Parameter | Value |
|---|---|
| Radius | the lens size; softens shadows only |
| Clearance | centre at least radius + 2 mm from any surface |
| Near-field limit | pattern approximate closer than ~5× the lens size |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| IES light blown out | host power left at 1 W | 0.2604 W (step 3) |
| Much dimmer than the hand calculation | the light's sphere sits partly inside a ceiling or housing | clearance (table) |
| Beam shape wrong, too wide and soft | hosted on an area light | point or spot host (step 3) |
| Asymmetric beam points the wrong way | C-planes not aligned | aim by −Y and −X (step 4) |
| A long fixture lights like a spot | one light for the whole run | split it (step 5) |

Generic render problems are in troubleshooting.md.
