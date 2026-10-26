"""Map measure; canonical implementation behind pbr."""

import os

import bpy

def solve_levels(path, target_rgb, gamma=0.5):
    """'Measured levels': per-channel gain that lands the map's
    mean linear colour, after a shared gamma, on a target albedo. Returns the gain."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(-1, img.channels)[:, :3].astype(np.float64)
    if not img.is_float:   # byte images come back sRGB-encoded, not linear (api-traps)
        rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    mean = (rgb ** gamma).mean(axis=0)
    return tuple(float(t / max(m, 1e-4)) for t, m in zip(target_rgb, mean))

def map_mean(tex_id):
    """Linear mean RGB of a Poly Haven diff map; measured once, then cached in meta.json."""
    import core.archviz as archviz
    from core.archviz import library, read_meta
    folder = archviz.library("polyhaven", "textures", tex_id)
    meta = archviz.read_meta(folder)
    if "diff_mean_linear" in meta:
        return tuple(meta["diff_mean_linear"])
    import numpy as np
    img = bpy.data.images.load(os.path.join(folder, meta["maps"]["diff"]), check_existing=True)
    px = np.empty(img.size[0] * img.size[1] * img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(-1, img.channels)[:, :3].astype(np.float64)
    if not img.is_float:   # byte images hold sRGB-encoded values
        rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    mean = tuple(round(float(v), 4) for v in rgb.mean(0))
    meta["diff_mean_linear"] = list(mean)
    archviz.write_meta(folder, meta)
    return mean
