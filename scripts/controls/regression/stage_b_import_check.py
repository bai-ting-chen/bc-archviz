"""Smoke-test the import statements used by callers of Stage B compatibility facades."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import ast
import importlib
from pathlib import Path
import sys

FACADES = ('effects.caustics.caustic_photons', 'scene.lighting.interior', 'scene.environment.scatter',
           'effects.caustics.gn_caustics', 'materials.glass.glassware', 'renderer.finals.finals',
           'scene.environment.terrain', 'blend_refs', 'materials.water.film', 'materials.water.foot',
           'materials.water.mesh', 'materials.water.shading', 'materials.water.fragments')


def check():
    """Import each facade and every caller's relevant import, without running caller commands."""
    scripts = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(scripts / 'blender'))
    sys.path.insert(0, str(scripts / 'blender' / 'scene' / 'io'))   # blend_refs imports its siblings by name
    for name in FACADES:
        importlib.import_module(name)
    checked = []
    for path in sorted(scripts.rglob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            module = ''
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level and 'materials.water' in path.parts:
                    module = 'materials.water' + ('.' + module if module else '')
                relevant = module in FACADES or (module == 'materials.water' and any('water.' + a.name in FACADES for a in node.names))
                if relevant:
                    # Relative imports need the caller's package, available without executing its command.
                    namespace = {'__package__': 'materials.water' if 'materials.water' in path.parts else None}
                    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
                    checked.append(str(path.relative_to(scripts)) + ':' + str(node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FACADES:
                        importlib.import_module(alias.name)
                        checked.append(str(path.relative_to(scripts)) + ':' + str(node.lineno))
    # Ground shaders depend on terrain's private helpers, not only its public API.
    for name in ('materials.ground.ground', 'materials.ground.meadow_ground', 'materials.water.build', 'effects.caustics.gn_caustics'):
        importlib.import_module(name)
    print('STAGE B IMPORT SMOKE:', len(checked), 'caller import statements; 13 facades')
    return checked


if __name__ == '__main__':
    check()
