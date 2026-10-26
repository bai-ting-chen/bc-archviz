"""Cycles finals in the open UI with no sample/time limit (RULES GAT_04), and post-processing from the
saved passes. LuxCore finals: from_passes.py. pipeline.md > Final render in the open UI.

    # in the open UI (via MCP), after building the scene:
    import finals; finals.start_in_ui(out_dir, (2400, 3000))
    # headless test with exactly the final settings (RULES GAT_04 (4)):
    blender -b scene.blend --python finals.py -- test <spp> <out_dir> <W>x<H>
    # after the user stops it:
    blender -b --factory-startup --python finals.py -- denoise <passes.exr> <denoised.exr>
    blender -b scene.blend --python finals.py -- png <denoised.exr> <out_base>

Traps it handles (render-settings.md):
- Cycles auto-tiling finishes each 2048 px tile before the next: with no sample limit only the
  first tile ever renders. Auto-tile off AND tile size above the frame (a 3200x4000 frame still
  showed 4 tiles in the UI with auto-tile off).
- A stop from the viewer may fire render_complete yet skip the denoiser (saved Combined ==
  Noisy Image); Esc fires render_cancel and skips the compositor. Both handlers save every pass,
  and `denoise` rebuilds the image with OIDN from Noisy Image + Denoising Albedo + Normal.
- A multilayer image reports size 0 until its pixels load: read the size with OpenImageIO.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from renderer.finals.final_settings import setup_unlimited  # noqa: F401
from renderer.finals.final_session import _STATE, _save, _on_complete, _on_cancel, remove_handlers, start_in_ui, stop_in_ui  # noqa: F401
from renderer.finals.final_images import denoise_from_passes, png_from_exr  # noqa: F401
import os
import sys

import bpy


if bpy.app.background and "--" in sys.argv and os.path.basename(__file__) in " ".join(sys.argv):
    a = sys.argv[sys.argv.index("--") + 1:]
    if a and a[0] == "test":
        sc = setup_unlimited(tuple(int(v) for v in a[3].split("x")), int(a[1]))
        sc.render.filepath = os.path.join(a[2], "finaltest_passes.exr")
        bpy.ops.render.render(write_still=True)
        f = sc.render.image_settings
        f.media_type = "IMAGE"; f.file_format = "PNG"; f.color_depth = "8"
        bpy.data.images["Render Result"].save_render(os.path.join(a[2], "finaltest.png"), scene=sc)
        print("TEST DONE")
    elif a and a[0] == "denoise":
        print("DENOISED", denoise_from_passes(a[1], a[2]))
    elif a and a[0] == "png":
        print("PNG", png_from_exr(a[1], a[2]))
