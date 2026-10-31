"""Scan final scenes through headless Blender without changing them."""
import json
import subprocess
import tempfile
from pathlib import Path
from study_files import checked


def scan(scenes, study, blender):
    """Return a stable reference snapshot and used paths, rejecting every unsafe reference."""
    snapshot, used, errors = {}, set(), []
    script = Path(__file__).resolve().parents[1] / 'blender/scene/io/blend_refs.py'
    with tempfile.TemporaryDirectory(prefix='bc-close-refs-') as temp:
        for scene in scenes:
            out = Path(temp) / 'refs.json'
            result = subprocess.run([blender, '-b', str(scene), '--factory-startup', '--python-exit-code', '1',
                                     '--python', str(script), '--', '--out', str(out)], capture_output=True, text=True)
            if result.returncode or not out.exists():
                raise RuntimeError(f'Blender scan failed: {scene}\n{result.stdout}\n{result.stderr}')
            rows = json.loads(out.read_text(encoding='utf-8'))
            snapshot[scene.name] = rows
            out.unlink()
            for _, _, _, files in rows:
                for filename in files:
                    path = Path(filename)
                    reason = 'missing' if not path.exists() else None
                    try:
                        checked(path, study)
                    except ValueError:
                        reason = 'outside study or linked path'
                    if path.is_relative_to(study / '_wip'):
                        reason = 'under _wip/'
                    if reason:
                        errors.append(f'{filename}: {reason}')
                    used.add(path)
    if errors:
        raise ValueError('unsafe references:\n' + '\n'.join(sorted(set(errors))))
    return snapshot, used
