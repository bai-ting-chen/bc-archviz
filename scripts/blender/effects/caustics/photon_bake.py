"""Photon bake; implementation for caustic_photons."""
import numpy as np
from effects.caustics.photon_grid import GRID, _save_grid, _load_grid


def bake_irradiance(npy_paths, exr_path, sigma_cells=1.0):
    """Merge photon grids, smooth by sigma_cells, write the irradiance EXR (W/m2)."""
    import bpy
    _load_grid(npy_paths[0])
    # each worker's grid is already a full estimate (photon power uses that worker's own n): AVERAGE
    grid = sum(np.load(p) for p in npy_paths) / len(npy_paths)
    cell = GRID["size"] / GRID["res"]
    E = grid / (cell * cell)                                  # W/m2 per cell
    if sigma_cells > 0:                                       # photon-map style kernel
        k = int(3 * sigma_cells) + 1
        x = np.arange(-k, k + 1)
        g1 = np.exp(-0.5 * (x / sigma_cells) ** 2)
        g1 /= g1.sum()
        E = np.apply_along_axis(lambda r: np.convolve(r, g1, mode="same"), 1, E)
        E = np.apply_along_axis(lambda c: np.convolve(c, g1, mode="same"), 0, E)
    res = GRID["res"]
    img = bpy.data.images.get("CAUSTIC_E") or bpy.data.images.new("CAUSTIC_E", res, res,
                                                                   float_buffer=True, alpha=False)
    px = np.zeros((res, res, 4), dtype=np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = E
    px[..., 3] = 1.0
    img.pixels.foreach_set(px.ravel())
    # NOT img.save(): for generated float images it bakes the scene view transform + exposure into
    # the file (a 100 W/m2 spike came back as 7.1). save_render with explicit EXR settings is exact.
    s = bpy.context.scene.render.image_settings
    prev = (s.file_format, s.color_depth, s.exr_codec)
    s.file_format, s.color_depth, s.exr_codec = "OPEN_EXR", "32", "ZIP"
    img.save_render(exr_path)
    _save_grid(exr_path)
    s.file_format, s.color_depth, s.exr_codec = prev
    img.filepath_raw = exr_path
    img.source = "FILE"
    img.colorspace_settings.name = "Non-Color"
    img.reload()
    return {"E_max_W_m2": float(E.max()), "E_p99_W_m2": float(np.quantile(E[E > 0], 0.99)) if (E > 0).any() else 0.0}
