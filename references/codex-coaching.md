# Coaching: the judgement Claude applies, written down for Codex

The goal is that Codex makes the same render calls Claude would (RULES 15b). Each lesson below
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
- **Aim a camera at the thing.** Use a Track To constraint on an empty placed at the feature's
  real coordinates, rather than guessed rotations. Then check the feature lands inside the frame
  (`world_to_camera_view`) before rendering.

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
  reference (RULES 8, 8b).
- **Name the character, not only the mean:** feature size, edge sharpness, contrast, density,
  orientation, distribution. A metric that passes while the image looks wrong means the metric is
  wrong.
- **Show the user the best state after a few rounds** (the study's cap), rather than tuning blind.
  Metric checklists are evidence for a look decision, never a replacement for it.
