"""Second-opinion review of a skill change by Codex (read-only), before the change is pushed.

The agent that writes the code runs it once (syntax, one run, the control render) and does
not review it; Codex reads it against the skill's own rules (references/maintaining.md).

    python scripts/codex_review.py --commit <sha>      # one commit
    python scripts/codex_review.py --uncommitted       # working tree
    python scripts/codex_review.py --base origin/main  # everything not yet pushed

Prints Codex's findings; nothing is written. Needs the Codex CLI (desktop app or npm).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMPT = """Review this change to the blender-archviz skill (Blender 5.2 archviz pipeline).
Read SKILL.md, RULES.md, references/maintaining.md and references/api-traps.md first.
Report, most severe first, each with file:line and a concrete failure scenario:
1. Correctness bugs in the code: wrong Blender 5.2 API use (see api-traps.md), broken
   node links, unit errors (mm vs m, lux, lumens, EV), paths that only work on one machine.
2. Breaks of the skill's own rules: a project, study, client or user-folder name in the skill;
   a scene-specific number presented as a rule (RULES 0); a rule stated outside RULES.md
   instead of pointed to; a push without a MIGRATE.md section; a second builder for a job
   that already has one; a new public helper without a one-line docstring.
3. Docs that no longer match the code (SKILL.md tables, references, helpers.md).
Do not report style preferences. Do not edit anything. If nothing survives, say so."""


def codex_exe():
    """The Codex CLI: on PATH, else the newest one the desktop app installed."""
    exe = shutil.which("codex")
    if exe:
        return exe
    found = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\OpenAI\Codex\bin\*\codex.exe"))
    if not found:
        sys.exit("Codex CLI not found (install the Codex app or `npm i -g @openai/codex`).")
    return max(found, key=os.path.getmtime)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit")
    g.add_argument("--uncommitted", action="store_true")
    g.add_argument("--base")
    ap.add_argument("--effort", default="high", help="model_reasoning_effort for the review")
    ap.add_argument("--extra", default="", help="extra review instructions appended to the prompt")
    a = ap.parse_args()

    cmd = [codex_exe(), "review",
           "-c", f'model_reasoning_effort="{a.effort}"',
           "-c", 'sandbox_mode="read-only"']
    if a.commit:
        cmd += ["--commit", a.commit]
    elif a.uncommitted:
        cmd += ["--uncommitted"]
    else:
        cmd += ["--base", a.base]
    cmd.append(PROMPT + ("\n" + a.extra if a.extra else ""))
    # stdin closed: codex otherwise waits for more input
    r = subprocess.run(cmd, cwd=SKILL, stdin=subprocess.DEVNULL)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
