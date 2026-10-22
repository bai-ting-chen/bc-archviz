# Coaching: the judgement Claude applies, written down for Codex

The goal is that Codex makes the same render calls Claude would (RULES AGT_03). Each lesson below
began as a gap: Claude caught something that Codex's own report or review missed. Read this file
before every stage report and every review. Craft facts (materials, light, water) go into their
topic reference; this file holds **how to look and how to check**.

## The training loop
1. **Codex judges first.** Every stage report ends with a *Self-judgement* section:
   - what in the output still differs from the reference or the design intent, worst first;
   - what you would do next, and why.

   Look at the images yourself before writing it.
2. **Claude judges second and compares.** Where Claude's verdict differs, Claude writes the gap
   here as a lesson: what was missed, the general principle, and how to check it next time.
   Lessons that are pure craft go to the topic reference instead, with a one-line pointer here.
3. **The lesson becomes a check.** Lessons are written as checks you can run, not advice.
4. **Graduation.** When Codex's self-judgement matches Claude's verdict, stage after stage, Claude
   hands that kind of decision to Codex. Claude notes in the study what was handed over.

## Checking your own change
- **Check the design intent across every object, not only the face you edited.** A cut, move or
  trim applies to every part that crosses the line. Query every object's bounding box against the
  intent, e.g. "nothing projects past the wall face" or "no water outside the pour".
  - The trap: you cut back a gutter's floor slab and left its end caps hanging 600 mm in the air.
- **An image that does not answer its question is a failed output**, even if it rendered. Before
  reporting, write one line per image: "this shows X". If you can't, fix the image.
- **Two failed fixes of one technique usually mean the technique is wrong.** Consider a different
  method before a third variant of the same idea (a habit, not a rule).
  - The trap: camera clipping gave an empty section twice. A boolean intersect of each object with
    a thin slab gives a real solid cut at once.
- **Look at the whole frame of every ON/OFF pair, not only the feature's crop.** Make the difference
  image, threshold it, and list every connected region outside the feature's expected area. A
  displacement, modifier or geometry change can break one element far from where you are looking.
  - The trap: a relief control was judged on wall crops; one board end, bottom left of the frame,
    displaced several cm into a wedge on the deck — builder, reviewer and director all missed it.
- **Look up the API before the one allowed run.** Before writing render or output setup, grep
  [api-traps.md](../scene/api-traps.md) for the property and reuse the skill's helpers (`finals.py` savers) or the study's
  last working script; probe the scene in-process before spending a frame.
  - The trap: a stage with one launch died on `obj.cycles.use_adaptive_subdivision` (moved to the
    modifier) and its rerun on the `OPEN_EXR_MULTILAYER` enum — both already in [api-traps.md](../scene/api-traps.md).
- **Aim a camera at the thing.** Use a Track To constraint on an empty placed at the feature's
  real coordinates, rather than guessed rotations. Then check the feature lands inside the frame
  (`world_to_camera_view`) before rendering.
- **A user-named asset or method is fixed, not replaced.** When the asset the user chose causes a
  defect, fix it inside that asset (crop, mask, re-sample, filter) and report; swapping it for
  another source is a user decision — ask through the director.
  - The trap: a plank scan's own plank ends gave false short joints; the builder replaced the scan
    with procedural noise, and the grain the user had asked to see disappeared.

## Making images someone must judge
- **A geometry check image:**
  - flat colour per layer or material;
  - studio light, with cavity or shadow so edges read;
  - the thing being approved large in frame, with enough context to place it;
  - the same camera for every variant;
  - variants side by side on one labelled sheet.

  Grey on grey hides exactly what is being checked.
- **A section** is a true cut. Use camera `clip_start`/`clip_end`, or a boolean on a copy. Frame it
  on the part in question and check it shows that part before reporting.

## Reviewing (reviewer role)
- **Review the output against the design intent, not only the code against the brief.** Open the
  images and the geometry numbers.
  - The trap: a review checked the capture code and passed a variant whose end caps stuck out past
    the wall, a fault visible in its own close-up image.

## Look judgement (render rounds)
- **Judge the final camera first,** then native-resolution crops beside the same crops of the
  reference (RULES MAT_03, VAL_01).
- **Name the character, not only the mean:** feature size, edge sharpness, contrast, density,
  orientation, distribution. A metric that passes while the image looks wrong means the metric is
  wrong.
- **Match the contrast, not only the mean.** Beside every mean you match, report the local
  standard deviation and the 2–98 % percentile spread of the same crop in ours and the reference
  (a crop free of foliage or other objects). A material whose mean matches but whose SD is several
  times lower reads as a blank, washed-out surface, however correct its pattern is in a macro view.
  - The trap: board-formed concrete matched the reference's display mean with an SD ~10× lower
    than the reference's — grain, joints and pits were invisible in the final view,
    and the self-judgement called it "subtler" instead of failing it.
- **A patch sheet with no candidate like the reference stops the stage.** Before spending the
  full-view run, ask of the patch sheet: does any candidate share the reference's character? If
  none does, report and stop; the full view of a failed patch only confirms the failure.
  - The trap: every patch showed straight barcode streaks beside the reference's torn ribbons; the
    best of them still went to a 2400 px view, which read as chrome.
- **Name the mechanism, not only the symptom.** A self-judgement that says "metallic strands" should
  also say why (here: ropes constant along their length act as cylinders that mirror one band of
  the surroundings) — the next step follows from the cause, not from the look.
- **Show the user the best state after a few rounds** (the study's cap), rather than tuning blind.
  Metric checklists are evidence for a look decision, never a replacement for it.


## AGT_03 procedure

**Train Codex towards Claude's judgement.** The goal is for Codex to make the same render calls
    Claude would.
    - Every Codex stage report ends with Codex's own self-judgement against the reference and the
      design intent.
    - Claude compares it with its own verdict and writes each gap as a checkable lesson:
      - working and judging habits go in [codex-coaching.md](codex-coaching.md);
      - craft goes in the topic reference.
    - A kind of decision moves to Codex once its self-judgement keeps matching Claude's.
    - **Normal mode by default.** Training costs extra tokens on both sides, so CPM (AGT_02) skips the
      self-judgement and the lesson writing unless the user asks for training in CPM.
