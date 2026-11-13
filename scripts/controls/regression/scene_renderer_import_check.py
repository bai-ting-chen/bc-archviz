"""Smoke-test the import statements used by callers of Stage B compatibility facades."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import ast
import importlib
from pathlib import Path
import sys

FACADES = ('scene.lighting.interior', 'scene.environment.scatter',
           'effects.caustics.geometry_node_caustics', 'materials.glass.glassware', 'renderer.finals.finals',
           'scene.environment.terrain', 'blend_references', 'materials.water.falling_film', 'materials.water.pool_impacts',
           'materials.water.mesh_builders', 'materials.water.surface_shading', 'materials.water.film_fragments')


def check():
    """Import each facade and every caller's relevant import, without running caller commands."""
    scripts = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(scripts / 'blender'))
    sys.path.insert(0, str(scripts / 'blender' / 'scene' / 'io'))   # blend_references imports its siblings by name
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
    for name in ('materials.ground.ground', 'materials.ground.meadow_ground', 'materials.water.falling_film_assembly', 'effects.caustics.geometry_node_caustics'):
        importlib.import_module(name)
    print('STAGE B IMPORT SMOKE:', len(checked), 'caller import statements; 12 facades')
    return checked


if __name__ == '__main__':
    check()
