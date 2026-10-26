# Validation


## VAL_01 procedure

**Detail pass at native resolution**. Region means match long
before the image does. Once they agree, crop each material/effect at full resolution beside
the same crop of the reference and judge its *character*: feature size, edge sharpness,
contrast, density, orientation, distribution — a feature can match in mean and still read
wrong in character. Repeat after every change to that feature; half-res pairs hide it.


## VAL_02 procedure

**A control render is the only proof.** Feature OFF + same scene twice (noise floor; same seed
for the feature diff); read *changed > 2 %*, several times the noise floor, and look at a
diff/crop; verify the control really
removed the feature. Whole-frame averages hide local effects, and a broken control looks like
"no effect".


**Strength previews from one render.** For a colour layer built as a multiplier M with an AOV, a
preview at strength k is `beauty × (1 + k(M − 1)) / M` on linear EXRs. Apply it only where M is
plausible (e.g. 0.8–1.25), on dry opaque pixels: on transparent layers (water films, glass) the AOV
holds only a fraction of the surface behind, and the division turns into speckle. It ignores the
change in bounce light, so it chooses a strength; a render confirms it.

**Flat-wall lab for a look layer.** When a procedural look layer misses twice in full renders, build
it on a flat wall at real size with the unit joints drawn for scale (renders of seconds), iterate
against the reference, then install the exact node graph: `scripts/controls/effects/weathering_lab.py`.
For geometry layers seen at grazing angles (water films, their foot), the lab is a strip of the
real scene: the final camera with a render border around a short stretch (about a minute per
variant), one variant file per try and a side-by-side sheet.

**Judge at final-view pixels.** Before matching a reference, compute mm per pixel at the feature
in the final view (vertical and along a foreshortened wall separately). A close-up reference
shows detail that is sub-pixel in the shot; matching it adds features the final view cannot show
(and loses the ones it does). Crop the reference to the same footprint, or judge its look at the
final view's scale.

## VAL_03 procedure

Measure on the PNG the renderer wrote (`imgstats.py`, `refmatch.py`) — AgX rolls off whites,
so linear values mislead for look matching. Physical calibration controls may inspect linear EXR energy data. Process frames → study `_wip/`.


## VAL_04 procedure

Bisect odd behaviour in a minimal headless scene (`scripts/controls/`) before tuning the real
one — a small scene isolates the cause in minutes where the full scene hides it.

Check the crop/patch actually covers the changed feature before interpreting unchanged numbers.
Pack small GPU probes when possible; run only affected sections. Budget: one first run, one per real fix, one final.
