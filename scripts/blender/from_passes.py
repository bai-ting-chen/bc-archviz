# Final images from a multilayer passes EXR: DENOISED -> <base>.exr + AgX PNGs, Combined -> <base>_raw.exr.
#   blender -b --factory-startup --python from_passes.py -- <passes.exr> <base> [ev,ev,...]
# env RT_LOOK = AgX look (default "AgX - Medium High Contrast"). Use it whenever a final was cancelled
# from Blender (Esc, the status-bar X): that path skips the compositor, so the saved composite is raw.
import sys, os, bpy, OpenImageIO as oiio
a = sys.argv[sys.argv.index("--") + 1:]
src, base = a[0], a[1]; evs = [float(x) for x in (a[2] if len(a) > 2 else "-5.0,-4.5,-4.0").split(",")]
inp = oiio.ImageInput.open(src); ch = {}; s = 0
while inp.seek_subimage(s, 0):
    img = inp.read_image(oiio.FLOAT)
    for i, n in enumerate(inp.spec().channelnames): ch[n] = img[..., i]
    s += 1
inp.close()
import numpy as np
for key, path in (("ViewLayer.DENOISED", base + ".exr"), ("ViewLayer.Combined", base + "_raw.exr")):
    px = np.dstack([ch[key + "." + c] for c in "RGB"]).astype(np.float32)
    out = oiio.ImageOutput.create(path); out.open(path, oiio.ImageSpec(px.shape[1], px.shape[0], 3, oiio.FLOAT))
    out.write_image(px); out.close()
sc = bpy.context.scene
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = os.environ.get("RT_LOOK", "AgX - Medium High Contrast")
f = sc.render.image_settings; f.file_format = "PNG"; f.color_depth = "16"
im = bpy.data.images.load(base + ".exr")
for ev in evs:
    sc.view_settings.exposure = ev; im.save_render(base + "_agx_%+.1f.png" % ev, scene=sc)
print("REBUILT", base)
