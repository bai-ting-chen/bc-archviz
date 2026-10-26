"""Deterministic file and numeric controls for photon, final-image and reference helpers."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

from graph_dump import dump_material
from water_numeric_check import array


def check(out):
    """Trace both light types, roundtrip irradiance, save graded PNGs and localise a test reference."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender' / 'scene' / 'io'))
    import blend_refs
    import effects.caustics.caustic_photons as photons
    import renderer.finals.finals as finals
    result = {}
    geom = str(out / 'photons.npz')
    result['export'] = photons.export_geometry(geom, grid=dict(res=24, size=.9, x0=-.45, y0=-.45, z=.73))
    with np.load(geom, allow_pickle=True) as data:
        result['geometry'] = {k: data[k].tolist() for k in data.files}
    result['fresnel'] = [photons._fresnel(c, eta) for c in [0., .4, .8, 1.] for eta in [.75, 1.5]]
    paths = []
    for name, source in dict(sun=dict(type='sun', dir=[.2, .1, 1], half_angle_deg=.2665, irradiance=100),
                             area=dict(type='area', centre=[0, 0, 1.7], normal=[0, 0, -1], size=.1, power=50)).items():
        grid, stats = photons.trace(geom, 200, 42, source)
        result[name] = dict(grid=array(grid), stats=stats)
        path = str(out / (name + '.npy'))
        np.save(path, grid)
        photons._save_grid(path)
        paths.append(path)
    exr = str(out / 'irradiance.exr')
    result['bake'] = photons.bake_irradiance(paths, exr)
    mat = bpy.data.materials.new('photon receiver')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    bsdf.label = 'control albedo'
    color = nt.nodes.new('ShaderNodeRGB')
    nt.links.new(color.outputs[0], bsdf.inputs['Base Color'])
    photons.add_caustic_light(mat, exr, albedo_label='control albedo')
    photons.add_caustic_light(mat, exr, albedo_label='control albedo')
    result['receiver'] = dump_material(mat)
    # Compare PNG bytes and linear EXR pixels; EXR container metadata can vary.
    sc = bpy.context.scene
    finals.png_from_exr(exr, str(out / 'graded'))
    result['png_sha256'] = hashlib.sha256((out / 'graded.png').read_bytes()).hexdigest()
    img = bpy.data.images.load(exr, check_existing=False)
    px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(px)
    result['irradiance_pixels'] = array(px)
    finals.setup_unlimited((80, 100), 12)
    result['final_settings'] = dict(samples=sc.cycles.samples, tile=sc.cycles.tile_size,
                                    adaptive=sc.cycles.use_adaptive_sampling, size=[sc.render.resolution_x, sc.render.resolution_y],
                                    format=sc.render.image_settings.file_format, depth=sc.render.image_settings.color_depth)
    finals.remove_handlers()
    result['handlers'] = [len(bpy.app.handlers.render_complete), len(bpy.app.handlers.render_cancel)]
    result['unsaved_final_error'] = None
    try:
        finals.start_in_ui(str(out), (80, 100))
    except RuntimeError as error:
        result['unsaved_final_error'] = str(error)
    # Only owned scratch data may be saved/localised by this control.
    study = out / 'study'
    study.mkdir(exist_ok=True)
    source = out / 'outside' / 'image.png'
    source.parent.mkdir(exist_ok=True)
    source.write_bytes((out / 'graded.png').read_bytes())
    image = bpy.data.images.load(str(source), check_existing=False)
    # Restrict reference testing to this image; every other image belongs to the other controls.
    for other in list(bpy.data.images):
        if other != image and other.name not in ('Render Result', 'Viewer Node'):
            bpy.data.images.remove(other)
    bpy.ops.wm.save_as_mainfile(filepath=str(study / 'references.blend'))
    result['localised'] = blend_refs.localise(str(study))
    result['localised_bytes'] = hashlib.sha256(Path(bpy.path.abspath(image.filepath)).read_bytes()).hexdigest()
    result['refs'] = [[type(d).__name__, attr, path] for d, attr, path in blend_refs.references()]
    result['udim'] = blend_refs.files_of(type('Tiled', (), dict(source='TILED', tiles=[type('Tile', (), dict(number=1001))()]))(), 'image.<UDIM>.exr')
    # Paths differ between runs; preserve their relative meaning in the baseline.
    def relative(v):
        if isinstance(v, str):
            return v.replace(str(out), '<OUT>').replace(str(out).replace('\\', '/'), '<OUT>')
        if isinstance(v, list):
            return [relative(x) for x in v]
        if isinstance(v, dict):
            return {k: relative(x) for k, x in v.items()}
        return v
    return relative(result)
