"""Draw Rhino model edges (from scripts/rhino/project_edges.py) over the reference image.

    python scripts/edge_overlay.py edges.json ref.png out.png [--w 1000]

The reference is resized to the width the edges were projected at (--w, its own aspect kept),
washed 35 % toward white, and each layer drawn in its own colour. Run with the MCP venv python.
Check the geometry against this BEFORE the Rhino approval gate (RULES GAT_01)."""
import argparse
import colorsys
import json
import zlib

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("edges"); ap.add_argument("ref"); ap.add_argument("out")
ap.add_argument("--w", type=int, default=1000)
a = ap.parse_args()
ref = Image.open(a.ref).convert("RGB")
ref = ref.resize((a.w, round(a.w * ref.height / ref.width)))
ref = Image.blend(ref, Image.new("RGB", ref.size, (255, 255, 255)), 0.35)
d = ImageDraw.Draw(ref)


def colour(layer):
    h = (zlib.crc32(layer.encode()) % 360) / 360.0
    return tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.9, 0.8))


with open(a.edges) as f:
    edges = json.load(f)
for lay, pts in edges:
    seg = []
    for p in pts + [None]:
        if p is None or abs(p[0]) > 5 * a.w or abs(p[1]) > 5 * a.w:
            if len(seg) > 1:
                d.line(seg, fill=colour(lay), width=2)
            seg = []
        else:
            seg.append(tuple(p))
ref.save(a.out)
print(a.out)
