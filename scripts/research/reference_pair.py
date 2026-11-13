"""Write side-by-side and overlaid image comparisons."""
from PIL import Image
from reference_image import load


def pair(render, reference_path, output_path, overlay=False):
    """Write a side-by-side render/reference pair or a half-strength overlay."""
    r = load(reference_path)
    a = load(render, r.size)
    if overlay:
        Image.blend(a, r, 0.5).save(output_path)
        return
    b = Image.new("RGB", (r.width * 2, r.height))
    b.paste(a, (0, 0))
    b.paste(r, (r.width, 0))
    b.resize((1400, round(1400 * r.height / (2 * r.width)))).save(output_path)
