# Study run

One look round's render: `scripts/workflow/study_run.py` rebuilds the study, renders a wip frame and
compares it with the reference. Choosing and judging rounds is validation's job (RULES VAL_02).

    python scripts/workflow/study_run.py <study> vNN.png [--rebuild] [--resolution-percent 50 --samples 128]
                                         [--reference _wip/ref.jpg] [--regions regions.json]

- **Runs** the study's `scene_look.py` (materials, lights, exposure) every time, and
  `scene_geometry.py` (import and camera) first with `--rebuild`.
- **Writes** `_wip/vNN.png`, the side-by-side `_wip/pair_vNN.png`, the render-over-reference
  `_wip/stack_vNN.png`, and saves the study `.blend`; prints the patch table when `regions.json`
  exists.
- **One change, one run**, at 50 % and 128 samples. Each version's reason lives as a comment on its
  own line above the value it changed.

## Editing the scene scripts
- The runner `ast.parse`s both scripts first. A scripted edit that appends `# reason` to a line
  continuing a call comments out the rest of it: put the comment on its own line above the value.
- Long patches go in a file with `assert old in s` per replacement, not a bash heredoc, so a stale
  anchor fails loudly; use the Edit tool for lines holding several statements.
- When patch scripts pile up, fold them back into the scene scripts before the study is reused.
