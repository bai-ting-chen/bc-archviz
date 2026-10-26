"""Read or localise milestone references through headless Blender."""
import os
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def refs(blend, study, blender, localise):
    """Run blend_refs.py in Blender; return its JSON."""
    out = os.path.join(study, '_close_refs.json')
    cmd = [blender, '-b', blend, '--factory-startup', '--python',
           os.path.join(os.path.dirname(HERE), 'blender', 'scene', 'blend_refs.py'), '--', '--study', study, '--out', out]
    if localise:
        cmd.append('--localise')
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = json.load(open(out, encoding='utf-8'))
    os.remove(out)
    return data
