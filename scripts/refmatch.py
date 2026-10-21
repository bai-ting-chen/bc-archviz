"""Match a render to a reference image (host side; run with the MCP venv python: numpy + Pillow).

    refmatch.py grid    <ref> <out.png> [--step 50]            reference with a 0..1 grid, for reading
                                                               vanishing points and solving the camera
    refmatch.py pair    <render> <ref> <out.png> [--overlay]   side by side (or 50 % blend for framing)
    refmatch.py patches <ref> <regions.json> <render> [...]    mean sRGB + luminance per named region

regions.json: {"oak": [x0, y0, x1, y1], ...} in 0..1 fractions of the frame (y from the top).
Images are compared at the reference's aspect, 1000 px wide. Balance lights region by region
before touching exposure (RULES RES_03).
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

W = 1000


def load(path, size=None):
    im = Image.open(path).convert("RGB")
    if size is None:
        size = (W, round(W * im.height / im.width))
    return im.resize(size, Image.LANCZOS)


def grid(ref, out, step=50):
    im = load(ref)
    d = ImageDraw.Draw(im)
    for i in range(0, max(im.size), step):
        major = i % (step * 5) == 0
        d.line([(i, 0), (i, im.height)], fill=(255, 0, 0) if major else (90, 0, 0))
        d.line([(0, i), (im.width, i)], fill=(0, 255, 0) if major else (0, 90, 0))
    im.save(out)


def pair(render, ref, out, overlay=False):
    r = load(ref)
    a = load(render, r.size)
    if overlay:
        Image.blend(a, r, 0.5).save(out)
        return
    b = Image.new("RGB", (r.width * 2, r.height))
    b.paste(a, (0, 0))
    b.paste(r, (r.width, 0))
    b.resize((1400, round(1400 * r.height / (2 * r.width)))).save(out)


def patches(ref, regions_path, renders):
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


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "grid":
        grid(a[1], a[2], int(a[a.index("--step") + 1]) if "--step" in a else 50)
    elif a[0] == "pair":
        pair(a[1], a[2], a[3], overlay="--overlay" in a)
    elif a[0] == "patches":
        patches(a[1], a[2], a[3:])
    else:
        sys.exit(__doc__)
