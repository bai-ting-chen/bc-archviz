"""Cycles finals in the open UI with no sample/time limit (RULES GAT_03), and post-processing from the
saved passes. LuxCore finals: from_passes.py. pipeline.md > Final render in the open UI.

    # in the open UI (via MCP), after building the scene:
    import finals; finals.start_in_ui(out_dir, (2400, 3000))
    # headless test with exactly the final settings (RULES GAT_03 (4)):
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
import os
import sys

import bpy

_STATE = {}


def setup_unlimited(res, samples=1_000_000, denoiser="OPENIMAGEDENOISE"):
    """Final settings: full res, untiled (tile > frame), no adaptive/time limit, denoiser + its passes stored, multilayer EXR."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.use_border = False
    c = sc.cycles
    c.device = "GPU"
    c.samples = samples
    c.use_adaptive_sampling = False
    c.time_limit = 0.0
    c.use_denoising = True
    c.denoiser = denoiser
    c.denoising_use_gpu = True                             # final denoising defaults to CPU
    c.use_auto_tile = False
    c.tile_size = max(4096, *res)                          # > frame: one tile even if Cycles tiles anyway
    sc.view_layers[0].cycles.denoising_store_passes = True
    f = sc.render.image_settings
    f.media_type = "MULTI_LAYER_IMAGE"; f.file_format = "OPEN_EXR_MULTILAYER"
    f.color_depth = "32"; f.exr_codec = "ZIP"
    return sc


def _save(scene, tag):
    out_dir, stem = _STATE["out_dir"], _STATE["stem"]
    os.makedirs(out_dir, exist_ok=True)
    rr = bpy.data.images["Render Result"]
    path = os.path.join(out_dir, f"{stem}_passes_{tag}.exr")
    rr.save_render(path, scene=scene)
    f = scene.render.image_settings
    f.media_type = "IMAGE"; f.file_format = "PNG"; f.color_depth = "16"
    rr.save_render(os.path.join(out_dir, f"{stem}_{tag}.png"), scene=scene)
    f.media_type = "MULTI_LAYER_IMAGE"; f.file_format = "OPEN_EXR_MULTILAYER"; f.color_depth = "32"
    print("FINAL SAVED", path)


def _on_complete(scene, *_):
    _save(scene, "complete"); remove_handlers()


def _on_cancel(scene, *_):
    _save(scene, "stopped"); remove_handlers()


def remove_handlers():
    """Unregister the final's save handlers (do this before cancelling a final you do not want saved)."""
    for lst, fn in ((bpy.app.handlers.render_complete, _on_complete), (bpy.app.handlers.render_cancel, _on_cancel)):
        for h in [h for h in lst if getattr(h, "__name__", "") == fn.__name__]:
            lst.remove(h)


def start_in_ui(out_dir, res, stem=None, samples=1_000_000):
    """Open UI: save the .blend, register savers (complete + cancel), render INVOKE_DEFAULT, fit the render view."""
    if not bpy.data.filepath:
        raise RuntimeError("save the .blend first: the final saves it and names its outputs after it")
    sc = setup_unlimited(res, samples)
    _STATE["out_dir"] = out_dir
    _STATE["stem"] = stem or os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    bpy.ops.wm.save_mainfile()
    remove_handlers()
    bpy.app.handlers.render_complete.append(_on_complete)
    bpy.app.handlers.render_cancel.append(_on_cancel)
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win):
        bpy.ops.render.render("INVOKE_DEFAULT")
    for w in bpy.context.window_manager.windows:          # a 3200 px frame opens at 1:1 - fit it
        for area in w.screen.areas:
            if area.type == "IMAGE_EDITOR":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=w, area=area, region=region):
                    bpy.ops.image.view_all(fit_view=True)
    return {"res": res, "samples": samples, "out": out_dir, "stem": _STATE["stem"]}


def stop_in_ui():
    """Stop the running render from its viewer (savers fire; the stop is asynchronous - wait for the passes file). Check afterwards whether the denoiser ran."""
    for w in bpy.context.window_manager.windows:
        for area in w.screen.areas:
            if area.type == "IMAGE_EDITOR":
                with bpy.context.temp_override(window=w, area=area):
                    bpy.ops.render.view_cancel()


def denoise_from_passes(src, out, layer="ViewLayer"):
    """OIDN (compositor Denoise, accurate prefilter, HDR) on a passes EXR's Noisy Image + albedo + normal -> linear EXR."""
    import OpenImageIO as oiio
    sc = bpy.context.scene
    img = bpy.data.images.load(src)
    spec = oiio.ImageInput.open(src).spec()                 # multilayer images report size 0 until loaded
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = spec.width, spec.height, 100
    tree = bpy.data.node_groups.new("DENOISE", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = tree.nodes, tree.links
    node = N.new("CompositorNodeImage"); node.image = img; node.layer = layer
    dn = N.new("CompositorNodeDenoise")
    for k, v in (("prefilter", "ACCURATE"), ("use_hdr", True), ("quality", "HIGH")):
        if hasattr(dn, k):
            setattr(dn, k, v)
    for name, s_ in (("Noisy Image", "Image"), ("Denoising Normal", "Normal"), ("Denoising Albedo", "Albedo")):
        L.new(node.outputs[name], dn.inputs[s_])
    go = N.new("NodeGroupOutput"); L.new(dn.outputs["Image"], go.inputs[0])
    sc.compositing_node_group = tree
    sc.render.use_compositing = True
    sc.render.use_sequencer = False
    for o in list(sc.objects):
        if o.type != "CAMERA":
            bpy.data.objects.remove(o)
    f = sc.render.image_settings
    f.media_type = "IMAGE"; f.file_format = "OPEN_EXR"; f.color_depth = "32"; f.exr_codec = "ZIP"
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    return out


def png_from_exr(exr, base):
    """16-bit PNG graded with the open scene's view transform, look, exposure and white balance."""
    sc = bpy.context.scene
    img = bpy.data.images.load(exr)
    f = sc.render.image_settings
    f.media_type = "IMAGE"; f.file_format = "PNG"; f.color_depth = "16"
    img.save_render(base + ".png", scene=sc)
    return base + ".png"


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
