"""Photon grid; implementation for caustic_photons."""
import json
import os


SURFACES = {"GLASS_TUMBLER": 1.52, "GLASS_WATER_INTERFACE": 1.52 / 1.333, "WATER_SURFACE": 1.333}


GRID = {"x0": -0.45, "y0": -0.45, "size": 0.90, "res": 900, "z": 0.7300}   # 1 mm cells


def _stem(path):
    return path[:-4] if path.lower().endswith((".npy", ".npz", ".exr")) else path


def _save_grid(path):
    """Write GRID next to a stage's output (<file>.grid.json) so the next stage, often a fresh
    Blender, uses the same receiver plane."""
    with open(_stem(path) + ".grid.json", "w") as f:
        json.dump(GRID, f)


def _load_grid(path):
    p = _stem(path) + ".grid.json"
    if os.path.exists(p):
        with open(p) as f:
            GRID.update(json.load(f))
