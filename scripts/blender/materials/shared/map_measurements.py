"""Map measure; canonical implementation behind pbr."""

import os

import bpy
import numpy as np


def image_rgb(img):
    """The image's first three channels as a float64 (pixels, 3) array, as Blender stores them."""
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(-1, img.channels)[:, :3].astype(np.float64)


def srgb_to_linear(rgb):
    """Decode sRGB-encoded 0–1 values to linear (byte images come back encoded: api-traps)."""
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def solve_levels(path, target_rgb, gamma=0.5):
    """'Measured levels': per-channel gain that lands the map's
    mean linear colour, after a shared gamma, on a target albedo. Returns the gain."""
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    rgb = image_rgb(img)
    if not img.is_float:
        rgb = srgb_to_linear(rgb)
    mean = (rgb ** gamma).mean(axis=0)
    return tuple(float(t / max(m, 1e-4)) for t, m in zip(target_rgb, mean))

def map_mean_linear_rgb(tex_id):
    """Linear mean RGB of a Poly Haven diff map; measured once, then cached in meta.json."""
    import core.archviz as archviz
    folder = archviz.library("polyhaven", "textures", tex_id)
    meta = archviz.read_meta(folder)
    if "diff_mean_linear" in meta:
        return tuple(meta["diff_mean_linear"])
    img = bpy.data.images.load(os.path.join(folder, meta["maps"]["diff"]), check_existing=True)
    rgb = image_rgb(img)
    if not img.is_float:
        rgb = srgb_to_linear(rgb)
    mean = tuple(round(float(v), 4) for v in rgb.mean(0))
    meta["diff_mean_linear"] = list(mean)
    archviz.write_meta(folder, meta)
    return mean
