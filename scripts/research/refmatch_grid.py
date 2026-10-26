"""Draw reading grids over reference images."""
from PIL import ImageDraw
from refmatch_image import load


def grid(ref, out, step=50):
    """Write a reference image with major and minor reading-grid lines."""
    im = load(ref)
    d = ImageDraw.Draw(im)
    for i in range(0, max(im.size), step):
        major = i % (step * 5) == 0
        d.line([(i, 0), (i, im.height)], fill=(255, 0, 0) if major else (90, 0, 0))
        d.line([(0, i), (im.width, i)], fill=(0, 255, 0) if major else (0, 90, 0))
    im.save(out)
