"""Deterministic file and numeric controls for final-image and reference helpers."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

from water_numeric_check import array


def check(out):
    """Roundtrip a float gradient EXR, save graded PNGs and read a test reference."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender' / 'scene' / 'io'))
    import blend_refs
    import renderer.finals.finals as finals
    result = {}
    exr = str(out / 'irradiance.exr')
    sc = bpy.context.scene
    img = bpy.data.images.new('control gradient', width=24, height=24, float_buffer=True)
    px = np.ones((24 * 24, 4), np.float32)
    px[:, :3] = np.linspace(0, 100, 24 * 24, dtype=np.float32)[:, None]
    img.pixels.foreach_set(px.ravel())
    settings = sc.render.image_settings
    previous = {k: getattr(settings, k) for k in ('file_format', 'color_mode', 'color_depth', 'exr_codec')}
    settings.file_format = 'OPEN_EXR'
    settings.color_mode = 'RGBA'
    settings.color_depth = '32'
    settings.exr_codec = 'ZIP'
    img.save_render(exr, scene=sc)
    for k, v in previous.items():
        setattr(settings, k, v)
    # Compare PNG bytes and linear EXR pixels; EXR container metadata can vary.
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
    # Only owned scratch data may be saved by this control.
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
