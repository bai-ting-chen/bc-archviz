"""Rebuild + render one look-dev frame of a study through the Blender MCP, then compare it.

    python scripts/study_run.py <study_dir> v07.png [--rebuild] [--pct 50] [--spp 128]
                              [--ref _wip/ref.jpg] [--regions regions.json]

The study holds scene_geometry.py (import + camera) and scene_look.py (materials, lights,
exposure). Both are syntax-checked first: a scripted edit that appends a "# reason" to a line
continuing a call comments its arguments out, and finding that after a render costs a round trip.
Writes <study>/_wip/<out>, a side-by-side _wip/pair_<out>, a stacked render-over-reference
_wip/stack_<out> (look at it every iteration: patch numbers miss joint grids, missing lamps,
black areas), prints refmatch patches, and saves <study>/<name>.blend. Run with the MCP venv python.
"""
import argparse
import ast
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))

RUNNER = '''
import bpy, os
STUDY = {study!r}
for f in {scripts!r}:
    exec(open(os.path.join(STUDY, f), encoding="utf-8").read(), {{"__name__": "__main__"}})
sc = bpy.context.scene
sc.render.resolution_percentage = {pct}
sc.cycles.samples = {spp}
sc.render.filepath = os.path.join(STUDY, "_wip", {out!r})
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(STUDY, {blend!r}))
result = {{"out": sc.render.filepath}}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study"); ap.add_argument("out")
    ap.add_argument("--rebuild", action="store_true", help="also run scene_geometry.py (re-import)")
    ap.add_argument("--pct", type=int, default=50); ap.add_argument("--spp", type=int, default=128)
    ap.add_argument("--ref", default="_wip/ref.jpg"); ap.add_argument("--regions", default="regions.json")
    a = ap.parse_args()
    study = os.path.abspath(a.study)
    scripts = (["scene_geometry.py"] if a.rebuild else []) + ["scene_look.py"]
    for f in scripts:
        with open(os.path.join(study, f), encoding="utf-8") as fh:
            src = fh.read()
        try:
            ast.parse(src, f)
        except SyntaxError as e:
            sys.exit(f"syntax error, nothing sent to Blender: {f}:{e.lineno}: {e.msg}\n  {e.text}")
    os.makedirs(os.path.join(study, "_wip"), exist_ok=True)
    blend = os.path.basename(study.rstrip("\\/")).split("_", 1)[-1] + ".blend"
    code = RUNNER.format(study=study, scripts=scripts, pct=a.pct, spp=a.spp, out=a.out, blend=blend)
    tmp = os.path.join(study, "_wip", "_run_now.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "mcp_call.py"), "execute_blender_code",
                            "--file", tmp], capture_output=True, text=True)
    finally:
        os.remove(tmp)
    text = r.stdout + r.stderr
    if '"status": "error"' in text or r.returncode:
        sys.exit("Blender error:\n" + text[-3000:].replace("\\n", "\n"))
    render = os.path.join(study, "_wip", a.out)
    ref = os.path.join(study, a.ref)
    if not os.path.exists(ref):
        print("rendered", render); return
    from PIL import Image
    rm = [sys.executable, os.path.join(TOOLS, "refmatch.py")]
    subprocess.run(rm + ["pair", render, ref, os.path.join(study, "_wip", "pair_" + a.out)])
    r_img = Image.open(ref).convert("RGB"); w, h = r_img.size; s = 1225 / w
    sw, sh = round(w * s), round(h * s)
    stack = Image.new("RGB", (sw, sh * 2))
    stack.paste(Image.open(render).convert("RGB").resize((sw, sh)), (0, 0)); stack.paste(r_img.resize((sw, sh)), (0, sh))
    stack.save(os.path.join(study, "_wip", "stack_" + a.out))
    regions = os.path.join(study, a.regions)
    if os.path.exists(regions):
        subprocess.run(rm + ["patches", ref, regions, render])
    print("rendered", render)


if __name__ == "__main__":
    main()
