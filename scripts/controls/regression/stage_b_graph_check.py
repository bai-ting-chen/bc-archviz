"""Saved graph, geometry and numeric baseline for Stage B Blender job modules.

Run in a factory-startup Blender with -- <output directory>. The water integration
and MNEE controls run too; their printed measurements are retained as stable JSON.
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'blender'))
sys.path.insert(0, str(HERE))
from graph_dump import dump_material, dump_tree, value, write
from water_numeric_check import array, object_mesh


def graphs(out):
    """Exercise lights, scatter, caustics, terrain and glass assembly through their old APIs."""
    import scene.lighting.atmosphere as atmosphere
    import materials.glass.glassware as glassware
    import effects.caustics.gn_caustics as gn_caustics
    import scene.lighting.interior as interior
    import scene.environment.scatter as scatter
    import scene.environment.terrain as terrain
    ies = out / 'control.ies'
    ies.write_text('IESNA:LM-63-2002\n[MANUFAC] Control\nTILT=NONE\n1 800 1 5 1 1 2 0 0 0 1 1 10\n0 45 90 135 180\n0\n200 150 50 10 0\n')
    result = dict(ies=interior.ies_read(str(ies)), luminance=interior.lens_luminance(800, .02))
    lights = [interior.downlight('control spot', (0, 0, 2)),
              interior.led_strip('control strip', (0, 0, 2), (1, 0, 2)),
              interior.panel_light('control panel', (0, 0, 2), (0, 0, 0)),
              interior.ies_light('control ies', str(ies), (0, 0, 2)),
              interior.ies_light('control ies spot', str(ies), (0, 0, 2), lumens=500, kind='SPOT')]
    interior.lit_once(lights)
    result['lights'] = {o.name: dict(type=o.data.type, energy=o.data.energy, color=list(o.data.color),
                                    temperature=o.data.temperature, location=list(o.location), rotation=list(o.rotation_euler),
                                    diffuse=o.visible_diffuse, transmission=o.visible_transmission,
                                    tree=dump_tree(o.data.node_tree) if o.data.node_tree else None) for o in lights}
    result['emitter'] = dump_material(interior.emitter('control emitter', 1000))
    result['emitter_color'] = dump_material(interior.emitter('control emitter color', 1000, color=(.2, .5, .8)))
    result['dots'] = dump_material(interior.emitter_dots('control dots', 1000))
    mat = bpy.data.materials.new('control ground')
    mat.use_nodes = True
    leaf = scatter.leaf_proto('control leaf', .07, .045, .012, mat)
    result['leaf'] = object_mesh(leaf)
    group = terrain.landform_group('control terrain', size=4, verts=9)
    result['terrain_graph'] = dump_tree(group)
    ter = terrain.add_terrain(group, mat, 'control terrain')
    result['height'] = [terrain.height(x, y, (0, 0), (4, 4)) for x, y in [(0, 0), (5, 5), (20, 10), (100, 100)]]
    result['scatter_graph'] = dump_tree(scatter.scatter_group())
    scatter.scatter([ter], leaf, .35, seed=3, patch=.42)
    sos = scatter.load_scatter_on_surface()
    meadow = scatter.meadow_layer_group(sos, 'control meadow')
    result['meadow_graph'] = dump_tree(meadow)
    cam = bpy.data.objects['Camera']
    result['frustum'] = scatter.frustum_tangents(cam, (400, 500))
    scatter.meadow_layer('control meadow object', meadow, ter, bpy.data.collections['PROTOS'], cam, Density=2.)
    result['caustic_graph'] = dump_tree(gn_caustics.caustic_sheet_group())
    result['caustic_material'] = dump_material(gn_caustics.caustic_sheet_material())
    receivers = bpy.data.collections.new('control receivers')
    occluders = bpy.data.collections.new('control occluders')
    bpy.context.scene.collection.children.link(receivers)
    bpy.context.scene.collection.children.link(occluders)
    sun = bpy.data.objects.new('control sun', bpy.data.lights.new('control sun', 'SUN'))
    bpy.context.scene.collection.objects.link(sun)
    overlay = gn_caustics.add_caustic_sheet(ter, receivers, occluders, sun)
    result['overlay'] = dict(mesh=object_mesh(overlay), material=dump_material(overlay.data.materials[0]))
    result['profiles'] = glassware.tumbler_profiles()
    for kind, objects in [('glass', glassware.glass_of_water(segments=12)),
                           ('mnee', glassware.glass_of_water_mnee(centre=(.3, 0), segments=12))]:
        result[kind] = {k: dict(mesh=object_mesh(v), material=dump_material(v.data.materials[0]))
                        if isinstance(v, bpy.types.Object) else v for k, v in objects.items()}
    fog = atmosphere.fog_volume(clear_boxes=[(-1, 1, -1, 1, 3)])
    result['fog'] = dump_material(fog.data.materials[0])
    return result


def main():
    """Write one deterministic control per affected facade, plus existing integration results."""
    from stage_b_import_check import check as import_check
    from stage_b_files_check import check as files_check
    from water_numeric_check import check as water_check
    import_check()
    out = Path(sys.argv[sys.argv.index('--') + 1])
    out.mkdir(parents=True, exist_ok=True)
    write(out / 'graphs.json', graphs(out))
    write(out / 'files.json', files_check(out))
    write(out / 'materials.water.json', water_check(out))
    # Existing controls reset the scene; run them after all graph/numeric snapshots.
    sys.argv = ['falling_film_check.py', '--', str(out), 'res=64', 'samples=2']
    runpy.run_path(str(HERE / 'falling_film_check.py'), run_name='__main__')
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        runpy.run_path(str(HERE / 'mnee_water.py'), run_name='__main__')
    measurements = [line for line in capture.getvalue().splitlines() if line.startswith('MNEE-TEST')]
    assert len(measurements) == 6
    write(out / 'mnee.json', measurements)
    print('STAGE B CONTROL COMPLETE')


if __name__ == '__main__':
    main()
