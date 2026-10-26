"""Load reference-sized RGB comparison images."""
from PIL import Image

W = 1000


def load(path, size=None):
    """Load RGB pixels at the requested size or the fixed reference width."""
    im = Image.open(path).convert("RGB")
    if size is None:
        size = (W, round(W * im.height / im.width))
    return im.resize(size, Image.LANCZOS)
