"""Final session; implementation for finals."""
import os
import bpy
from renderer.finals.final_settings import setup_unlimited


_STATE = {}


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
