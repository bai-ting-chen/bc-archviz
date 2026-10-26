"""Print regional display RGB and luminance comparisons."""
import json
import numpy as np
from refmatch_image import load


def patches(ref, regions_path, renders):
    """Print mean display RGB and luminance for every named image region."""
    with open(regions_path, encoding="utf-8") as f:
        regions = json.load(f)
    regions.setdefault("frame", [0, 0, 1, 1])
    size = load(ref).size
    for path in [ref, *renders]:
        a = np.asarray(load(path, size), dtype=float) / 255
        h, w = a.shape[:2]
        cells = []
        for name, (x0, y0, x1, y1) in regions.items():
            p = a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].reshape(-1, 3).mean(0)
            lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]
            cells.append(f"{name} {lum:.2f} ({p[0]:.2f},{p[1]:.2f},{p[2]:.2f})")
        print(path.replace("\\", "/").split("/")[-1][:16].ljust(16), " | ".join(cells))
