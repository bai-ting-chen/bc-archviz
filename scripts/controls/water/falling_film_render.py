"""Check the film integration thumbnail contains a visible signal."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import bpy
import numpy as np

def check_render(sc, OUT, checks):
    """Render and read back the original thumbnail."""
    sc.render.image_settings.media_type = 'IMAGE'; sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = str(OUT / 'falling_film_check.png'); bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(str(OUT / 'falling_film_check.png')); px = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(px)
    checks['render not empty'] = float(px[0::4].std()) > .02
