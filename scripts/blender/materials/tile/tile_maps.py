"""Tile face maps: find a face folder's albedo, roughness and height images, measure them in linear
light, and resolve their physical size. Results are cached on the image so rebuilds are cheap.
"""
import math
import json
import warnings
from pathlib import Path

import numpy as np
from core.archviz import read_meta


def find_maps(folder):
    """Find supported face albedo, roughness and height maps by filename."""
    paths = sorted(p for p in Path(folder).rglob('*') if p.suffix.lower() in
                   ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.exr', '.hdr', '.webp'))
    result = {}
    for key, tokens in (('color', ('diff', 'col')), ('rough', ('rough',)), ('height', ('disp', 'height'))):
        result[key] = next((p for p in paths if any(t in p.stem.lower() for t in tokens)), None)
    result['arm'] = next((p for p in paths if '_arm_' in p.stem.lower() or p.stem.lower().endswith('_arm')), None) if result['rough'] is None else None
    if result['color'] is None:
        raise ValueError('Face folder needs a *diff* or *col* albedo map')
    return result


def image_stats(image, color=False):
    """Cache linear RGB mean and maximum once per image and colour interpretation."""
    key = 'tile_surface_stats_' + ('color' if color else 'data')
    signature = json.dumps([list(image.size), image.channels, image.colorspace_settings.name, image.is_float])
    if image.get(key + '_signature') == signature and key in image:
        values = tuple(image[key])
        return values[:3], values[3:]
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    rgb = pixels.reshape(-1, image.channels)[:, :3].astype(np.float64)
    if rgb.shape[1] < 3:
        rgb = np.repeat(rgb[:, :1], 3, axis=1)
    if color and not image.is_float and image.colorspace_settings.name == 'sRGB':
        rgb = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    mean = tuple(float(max(x, 1e-8)) for x in rgb.mean(axis=0))
    maximum = tuple(float(x) for x in rgb.max(axis=0))
    image[key], image[key + '_signature'] = (*mean, *maximum), signature
    return mean, maximum


def mean_linear(image, color=False):
    """Return a cached linear RGB mean, including replicated single-channel maps."""
    return image_stats(image, color)[0]


def resolve_map_size(face, map_size):
    """Resolve physical map dimensions from metres or metadata in millimetres."""
    if map_size is None and face and (Path(face) / 'meta.json').exists():
        meta = read_meta(face)
        dimensions = meta.get('dimensions_mm') or meta.get('dimensions')
        if dimensions:
            if isinstance(dimensions, dict):
                dimensions = (dimensions['width'], dimensions['height'])
            map_size = tuple(float(x) / 1000 for x in dimensions[:2])
    if map_size is None:
        if face:
            warnings.warn('Face map dimensions missing; falling back to 1 x 1 m.', stacklevel=2)
        map_size = (1., 1.)
    size = tuple(map_size)
    if len(size) != 2 or any(not math.isfinite(x) or x <= 0 for x in size):
        raise ValueError('map_size must contain two positive finite metre dimensions')
    return (*size, 1.)


def warn_albedo(image, body, contrast=1., saturation=1.):
    """Warn when target normalization would exceed the face albedo cap."""
    mean, maximum = (np.asarray(x) for x in image_stats(image, True))
    maximum = mean + contrast * (maximum - mean)
    weights = np.asarray((.2126, .7152, .0722))
    mean = np.dot(mean, weights) * (1 - saturation) + mean * saturation
    maximum = np.dot(maximum, weights) * (1 - saturation) + maximum * saturation
    if any(peak * target / avg > .9 for peak, target, avg in zip(maximum, body, mean)):
        warnings.warn('Normalized face map exceeds 0.9; clamping can lower its mean albedo.', stacklevel=2)
