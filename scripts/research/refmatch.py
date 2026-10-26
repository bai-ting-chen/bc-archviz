"""Match a render to a reference image (host side; run with the MCP venv python: numpy + Pillow).

    refmatch.py grid    <ref> <out.png> [--step 50]            reference with a 0..1 grid, for reading
                                                               vanishing points and solving the camera
    refmatch.py pair    <render> <ref> <out.png> [--overlay]   side by side (or 50 % blend for framing)
    refmatch.py patches <ref> <regions.json> <render> [...]    mean sRGB + luminance per named region

regions.json: {"oak": [x0, y0, x1, y1], ...} in 0..1 fractions of the frame (y from the top).
Images are compared at the reference's aspect, 1000 px wide. Balance lights region by region
before touching exposure (RULES RES_03).
"""
import sys
from refmatch_image import load, W
from refmatch_grid import grid
from refmatch_pair import pair
from refmatch_patches import patches


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
