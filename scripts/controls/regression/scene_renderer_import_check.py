"""Smoke-test the import statements used by scene, renderer and water owner callers."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import ast
import importlib
from pathlib import Path
import sys

MODULES = (
    'scene.lighting.artificial',
    'scene.environment.scatter',
    'effects.caustics.geometry_node_caustics',
    'materials.glass.glassware',
    'renderer.finals.finals',
    'scene.environment.terrain',
    'blend_references',
    'materials.water.ballistic_sheet',
    'materials.water.falling_film_assembly',
    'materials.water.film_config',
    'materials.water.film_fields',
    'materials.water.film_fragments',
    'materials.water.film_surfaces',
    'materials.water.impact_bubbles',
    'materials.water.impact_config',
    'materials.water.impact_crowns',
    'materials.water.impact_drift',
    'materials.water.impact_foam',
    'materials.water.impact_locations',
    'materials.water.impact_splash',
    'materials.water.mesh_builders',
    'materials.water.motion_blur',
    'materials.water.pool_material',
    'materials.water.pool_ripples',
    'materials.water.ripple_bump',
    'materials.water.seeded_noise',
    'materials.water.water_mesh',
    'materials.water.wet_wall_proxy',
)


def check():
    """Import each owner and every caller's relevant import, without running caller commands."""
    scripts = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(scripts / 'blender'))
    sys.path.insert(0, str(scripts / 'blender' / 'scene' / 'io'))   # blend_references imports its siblings by name
    for name in MODULES:
        importlib.import_module(name)
    checked = []
    for path in sorted(scripts.rglob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            module = ''
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level and 'materials' in path.parts and path.parent.name == 'water':
                    module = 'materials.water' + ('.' + module if module else '')
                relevant = module in MODULES or (module == 'materials.water' and any('materials.water.' + a.name in MODULES for a in node.names))
                if relevant:
                    # Relative imports need the caller's package, available without executing its command.
                    namespace = {'__package__': 'materials.water' if 'materials' in path.parts and path.parent.name == 'water' else None}
                    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
                    checked.append(str(path.relative_to(scripts)) + ':' + str(node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in MODULES:
                        importlib.import_module(alias.name)
                        checked.append(str(path.relative_to(scripts)) + ':' + str(node.lineno))
    # Ground shaders depend on terrain's private helpers, not only its public API.
    for name in ('materials.ground.ground', 'materials.ground.meadow_ground', 'materials.water.falling_film_assembly', 'effects.caustics.geometry_node_caustics'):
        importlib.import_module(name)
    print('STAGE B IMPORT SMOKE:', len(checked), 'caller import statements; owner modules')
    return checked


if __name__ == '__main__':
    check()
