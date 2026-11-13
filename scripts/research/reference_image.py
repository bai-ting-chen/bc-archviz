"""Load reference-sized RGB comparison images."""
from PIL import Image

COMPARISON_WIDTH_PX = 1000


def load(path, size=None):
    """Load RGB pixels at the requested size or the fixed reference width."""
    im = Image.open(path).convert("RGB")
    if size is None:
        size = (COMPARISON_WIDTH_PX, round(COMPARISON_WIDTH_PX * im.height / im.width))
    return im.resize(size, Image.LANCZOS)
