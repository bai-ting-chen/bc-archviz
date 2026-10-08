"""Measure renders on the display-referred sRGB file.

    imgstats.py stats <img> [<img> ...]          frame: mean, p50, p99, clipping, black, R/B
    imgstats.py patch <img> x0 y0 x1 y1          same, inside a box given as 0..1 fractions
    imgstats.py diff  <a> <b>                    mean |a-b| x 100 (noise floor: render twice)
"""
import sys

import numpy as np
from PIL import Image


def load(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    return a


def describe(a, label):
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    rb = a[..., 0].mean() / max(a[..., 2].mean(), 1e-6)
    print(f"{label:40s} mean {lum.mean():.3f}  p50 {np.median(lum):.3f}  "
          f"p99 {np.quantile(lum, 0.99):.3f}  sigma {lum.std():.3f}  "
          f"clip {100 * (lum >= 0.995).mean():5.2f}%  black {100 * (lum <= 0.005).mean():5.2f}%  "
          f"R/B {rb:.2f}")


def main(argv):
    cmd = argv[0]
    if cmd == "stats":
        for p in argv[1:]:
            describe(load(p), p.replace("\\", "/").split("/")[-1])
    elif cmd == "patch":
        a = load(argv[1])
        h, w = a.shape[:2]
        x0, y0, x1, y1 = (float(v) for v in argv[2:6])
        describe(a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)],
                 f"patch {x0:.2f},{y0:.2f}-{x1:.2f},{y1:.2f}")
    elif cmd == "diff":
        a, b = load(argv[1]), load(argv[2])
        if a.shape != b.shape:
            sys.exit(f"size mismatch {a.shape} vs {b.shape}")
        d = np.abs(a - b).mean(axis=2)
        print(f"diff score {100 * d.mean():.3f}   p99 {100 * np.quantile(d, 0.99):.2f}   "
              f"changed>2% {100 * (d > 0.02).mean():.2f}% of pixels")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
