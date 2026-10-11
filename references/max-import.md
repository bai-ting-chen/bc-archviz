# 3ds Max (.max) assets → Blender

Vendor libraries (vegetation, furniture, props) often ship only as `.max` with V-Ray or Corona
materials. Blender reads them without 3ds Max through the **Import Autodesk MAX** extension plus
the repair pass in `scripts/blender/max_import.py`. Proved on four vegetation models of three
genera, 25–320 MB, 46k–971k faces; the checks below must pass on every new model.

## Install
- Extension `io_scene_max` (extensions.blender.org, community-maintained, GPL; verified 1.9.2).
  Download the zip, compare its sha256 with the platform's `archive_hash`
  (`https://extensions.blender.org/api/v1/extensions/?type=add-on`), then
  `blender -b -c extension install-file -r user_default --enable <zip>` and delete the zip.
  It lives in Blender's extension folder, never in a project (RULES 10d).
- `--factory-startup` turns extensions off: `max_import.load` enables it in the script.
- Reads Editable Mesh/Poly, primitives, VRayMtl, VRay2SidedMtl, Corona, Physical, Multi/Sub.
  Not: V-Ray proxies (`.vrmesh`), Forest Pack / RailClone scatter, GrowFX, modifier stacks.

## Workflow
```python
import max_import
objs, report = max_import.load(path, use_image_search=False, use_collection=True)
t = max_import.tidy(objs, unit_scale=0.01)        # Max system units: check the height is plausible
mats = max_import.rebuild_materials(objs, maps_dir)
```
Then light, camera and render as any scene. `transparent_max_bounces` 64 for stacked alpha
cards (foliage).

## What the importer gets wrong (repaired by `load`)
1. **Tube bands dropped.** Trunks, branches, twigs (any lofted tube) are stored as one record per
   band between two rings: ring A around to its seam, then ring B back
   (`[0,1,2,3,0, 4,7,6,5,4]`), with a UV per position. Blender's `validate()` drops them —
   13–28 % of all faces in the tested models, whole trunks and twigs missing. `load` rebuilds
   the strip with the record's UVs; rings that differ in vertex count (a tube tapering) are
   zipped by their u around the ring, quads where both step, triangles where one does.
   Reading a band as two end caps, or bridging rings with guessed UVs, puts discs inside every
   segment, leaves gaps in tapering trunks and squashes bark — both were tried and failed.
2. **Shifted material IDs.** The full per-face ID list is written onto the shorter polygon
   list, so after the first dropped face every ID belongs to a neighbour (leaf cards rendered
   as bark). Re-assigned face by face.
3. **Slot ≠ Max ID.** A Multi/Sub hands the importer a parameter block first, and a 2-sided sub
   takes two slots (front, back). `load` maps each ID to its sub's first slot; IDs wrap modulo
   the sub count as in Max; a sub the importer could not build is reported as
   `WARNING_ids_without_material`.
4. **UV channel.** Max channel 0 is vertex colour, 1 the UVs bitmaps read by default; the
   importer makes its first layer from whichever channel comes first. Render UV = channel 1.

## Checks — run on every new model before look-dev
- `report[i]`: `final_ids` per slot equal `raw_ids` mapped through `id_to_slot` for the faces
  that are not bands (leaf cards: exact); `restore_failed` 0; no `WARNING_ids_without_material`.
- `tidy(...)["loose_removed"]` 0 — loose vertices are faces that were not rebuilt.
- `open_loops(obj, material_index)` on bark: open rings only at the base, tips and fork-stem
  bases. A fork stem starting inside another tube is vendor construction; check that its ring
  sits inside the other surface (signed distance < 0 along that surface's normal).
- Texel density along and around a tube within ~2× of each other (UV length per metre ×
  texture pixels); a 10× difference is a broken UV, not the vendor's texture.
- Silhouette and branching against the vendor thumbnail; close-ups at native resolution (RULES 8b).

## Materials
The file's bitmap paths point at the vendor's machine; the materials are rebuilt in Blender
anyway (RULES 4). `rebuild_materials` finds the maps by the diffuse bitmap's stem in the
material name (`<max name>_<stem>_albedo` → `<stem>_{albedo,opacity,tran,glossiness,normal}`,
common suffix aliases accepted) and logs every fallback.
- **A wired V-Ray map overrides the scalar stored next to it.** The importer carries only the
  scalar (e.g. reflection glossiness 0.65). A needle card at roughness 0.35 glinted white at
  grazing sun; its glossiness map (0.136 in the needles → roughness ≥ 0.86) removes the
  glints and keeps the sheen (control: specular off vs map, same seed).
- Glossiness → roughness = 1 − gloss (Non-Color). Roughness maps wire directly.
- Leaf cards: Principled (albedo, roughness, normal, IOR 1.6) **+** Translucent (transmission
  map, else albedo), cut by the opacity map through Mix with Transparent. Green leaves reflect
  and transmit ~0.05–0.1 each in the visible, so Add stays energy-conserving; check the maps'
  linear means.
- Bark: albedo, roughness, normal, IOR 1.52. Vendor bark albedo maps can be dark (~0.04
  linear); compare with measured bark before a final.
- Vendor MAXScript material libraries (often obfuscated) are not run.
