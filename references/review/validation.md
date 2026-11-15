# Validation

Use when: running look rounds against a reference, proving a feature works, or a result looks odd.

Two questions decide every look round, and each is checked on its own: did the change reach its
target, and did anything else get worse. A round that helps its target but breaks something that
already matched has not gained anything.

## The look round (RULES VAL_02)

### 1. Before the first round: the match list
Write the list in `study-notes.md` › Match list, one line per thing the image must get right, each
with what passes it. Every round is judged against these lines, so a line too vague to fail
("looks right") gets rewritten until it can.
1. **Final-view pixels.** Compute mm per pixel at each feature in the final view, vertically and
   along a foreshortened wall. A close-up reference shows detail that is sub-pixel in the shot;
   matching it adds features the final view cannot show and loses the ones it does. Crop the
   reference to the same footprint, or judge its look at the final view's scale.
2. **Region lines.** About ten regions in 0..1 fractions in `regions.json` (each lit surface type,
   the shadow side, floor near and far, the background). Each passes when its ratio to the
   reference matches the others within the noise floor; exposure comes last (RULES RES_02), so
   ratios decide, not absolute means.
3. **Character lines.** Each material and effect at native resolution beside the same reference
   crop, judged on feature size, edge sharpness, contrast, density, orientation and distribution.
   A region can match in mean and still read wrong in character; half-resolution pairs hide it.
4. **Geometry lines.** What a region number cannot see: every object the reference shows is
   there, no surface is roofed or shaded by a member the reference does not have, joint grids
   and repeats read as in the reference.
5. **Feature lines.** Each effect claimed to work, passed only by its control (› Proving a feature).
6. **Noise floor.** Render the starting scene twice with the round settings and measure the
   difference (`image_statistics.py diff`). A change smaller than a few times that is noise.

### 2. One round
1. **Pick one failing line and make one change for it.** Region lines first (light, then
   material tone), then character, then the rest; within a group, the worst first. Light fixes
   follow `references/scene/reference-match.md` step 3.
2. **Render** with the study runner ([study-run.md](../workflow/study-run.md)).
3. **Check the target.** Its line moved toward the reference, in the number and in its crop.
4. **Check the rest against the best version so far.** `reference_match.py patches` on the
   reference, the best version and the new one; look at the stacked pair for the geometry lines.
   Every region that moved beyond the noise floor without being the target gets its crops
   compared with the best version. The numbers only say where to look; crops decide.
5. **Keep or revert.** The round passes when the target improved and no passing line got worse:
   the new version becomes the best. Otherwise put the changed value back to the best version's,
   so the next round starts from the best, not from the last.
6. **Log the round** in `_wip/loop-log.md`, one line: version, the change, the target line, kept
   or reverted, the line that failed and how (the character point or ratio by name), and the
   count of passing lines.

### 3. When to stop
- **Done:** every line on the match list passes in the best version, exposure is set, and each
  claimed feature has its control. A line whose number passes while its crop does not still fails.
- **Regressing:** two rounds in a row reverted. Go back to the best version and change the
  approach, not the value: a look layer that keeps missing goes to the lab
  (› Proving a feature); odd behaviour gets bisected (› Diagnosing odd behaviour); a method that
  cannot reach the line goes to the research loop (RULES RES_01).
- **Stuck:** three rounds without a new passing line. Stop and record why in the study notes.
- **Show the user** when done or stuck: the best version's
  stacked pair, the match list with each line's verdict, and in one or two lines what still fails.
  The look is approved by the user, not by the list.

## Proving a feature (RULES VAL_01)

**A control render is the only proof.** Render with the feature off, and the same scene twice for
the noise floor (same seed for the feature diff). Read *changed > 2 %*, several times the noise floor,
and look at a diff and a crop. Check that the control really removed the feature: whole-frame
averages hide local effects, and a broken control looks like "no effect". Check that the crop or
patch covers the changed feature before reading unchanged numbers.

Headless controls: `blender -b scene.blend --python scripts/blender/renderer/render_variant.py
-- out.png resolution=800x800 [displacement=off|caustics=off|wear=off|…|camera=NAME]` renders a saved
.blend with overrides on the GPU and never saves it. Its docstring lists every option; an unknown
option stops it rather than rendering an unchanged "control".

**Strength previews from one render.** For a colour layer built as a multiplier M with an AOV, a
preview at strength k is `beauty × (1 + k(M − 1)) / M` on linear EXRs. Apply it only where M is
plausible (e.g. 0.8–1.25), on dry opaque pixels: on transparent layers (water films, glass) the AOV
holds only a fraction of the surface behind, and the division turns into speckle. It ignores the
change in bounce light, so it chooses a strength; a render confirms it.

**Lab.** Build the layer on a flat wall at real size with the unit joints drawn for scale (renders
of seconds), iterate against the reference, then install the exact node graph:
`scripts/controls/effects/weathering_lab.py`. For geometry layers seen at grazing angles (water
films, their foot), the lab is a strip of the real scene: the final camera with a render border
around a short stretch (about a minute per variant), one variant file per try and a side-by-side
sheet.

## Measuring the rendered look

Measure on the PNG the renderer wrote (`scripts/review/image_statistics.py`,
`scripts/review/reference_match.py`): AgX rolls off whites, so linear values mislead for look
matching. Physical calibration controls may inspect linear EXR energy data. Processed frames go to
the study's `_wip/`.

## Diagnosing odd behaviour

Bisect odd behaviour in a minimal headless scene (`scripts/controls/`) before tuning the real one: a
small scene isolates the cause in minutes where the full scene hides it.
Pack small GPU probes when possible and run only the affected sections. Budget: one first run, one
per real fix, one final.
