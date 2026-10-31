# Validation

Use when: judging a look round against a reference, proving a feature works, or a result looks odd.

## The look round (iterative refinement)

### 1. Set the criteria before rendering
- **Where:** the regions to match and, per material or effect, the reference crop at the same
  footprint. Compute mm per pixel at the feature in the final view first (VAL_01 › Final-view pixels).
- **Which numbers decide:** the ratios between regions from `refmatch.py patches` on the PNG (VAL_03);
  exposure is set last (RULES RES_03), so match ratios, not absolute means. For a feature claim,
  *changed > 2 %* and several times the noise floor (VAL_02).
- **Which character points:** feature size, edge sharpness, contrast, density, orientation,
  distribution (VAL_01).

### 2. Loop
1. Render the wip frame with the study runner (`scripts/workflow/study_run.py`).
2. Measure the PNG the renderer wrote (VAL_03), then look at the stacked pair: region numbers miss
   joint grids, missing objects and wrongly roofed areas.
3. Ratios off: fix light or material region by region (lighting-camera.md › Recreating a
   reference) and go back to 1.
4. Ratios agree: compare native-resolution crops beside the reference (VAL_01), name the worst
   defect, fix only that, and go back to 1.
5. A change claimed to work gets its control render (VAL_02) before it counts.

### 3. When to stop (RULES VAL_05)
- **Done:** region ratios agree, exposure is set, every crop reads like the reference in character
  at final-view pixels, and each claimed feature has its control. A number that matches while the
  image does not is a fail.
- **A look layer missed twice in full renders:** move it to the flat-wall lab (VAL_02 › Lab).
- **Odd behaviour:** bisect it (VAL_04).
- **Stuck:** after 3 rounds without a clear gain, stop and record why (the research loop's rule).

## VAL_01 procedure

**Detail pass at native resolution.** Region means match long before the image does. Once they
agree, crop each material or effect at full resolution beside the same crop of the reference and
judge its *character*: feature size, edge sharpness, contrast, density, orientation, distribution.
A feature can match in mean and still read wrong in character. Repeat after every change to that
feature; half-res pairs hide it.

**Final-view pixels.** Before matching a reference, compute mm per pixel at the feature in the final
view (vertical and along a foreshortened wall separately). A close-up reference shows detail that is
sub-pixel in the shot; matching it adds features the final view cannot show (and loses the ones it
does). Crop the reference to the same footprint, or judge its look at the final view's scale.

## VAL_02 procedure

**A control render is the only proof.** Render feature OFF, and the same scene twice for the noise
floor (same seed for the feature diff). Read *changed > 2 %*, several times the noise floor, and look
at a diff and a crop. Verify the control really removed the feature: whole-frame averages hide local
effects, and a broken control looks like "no effect". Check the crop or patch actually covers the
changed feature before interpreting unchanged numbers.

**Strength previews from one render.** For a colour layer built as a multiplier M with an AOV, a
preview at strength k is `beauty × (1 + k(M − 1)) / M` on linear EXRs. Apply it only where M is
plausible (e.g. 0.8–1.25), on dry opaque pixels: on transparent layers (water films, glass) the AOV
holds only a fraction of the surface behind, and the division turns into speckle. It ignores the
change in bounce light, so it chooses a strength; a render confirms it.

**Lab.** When a procedural look layer misses twice in full renders, build it on a flat wall at real
size with the unit joints drawn for scale (renders of seconds), iterate against the reference, then
install the exact node graph: `scripts/controls/effects/weathering_lab.py`. For geometry layers seen
at grazing angles (water films, their foot), the lab is a strip of the real scene: the final camera
with a render border around a short stretch (about a minute per variant), one variant file per try
and a side-by-side sheet.

## VAL_03 procedure

Measure on the PNG the renderer wrote (`imgstats.py`, `refmatch.py`): AgX rolls off whites, so
linear values mislead for look matching. Physical calibration controls may inspect linear EXR energy
data. Processed frames go to the study's `_wip/`.

## VAL_04 procedure

Bisect odd behaviour in a minimal headless scene (`scripts/controls/`) before tuning the real one: a
small scene isolates the cause in minutes where the full scene hides it.
Pack small GPU probes when possible and run only the affected sections. Budget: one first run, one
per real fix, one final.
