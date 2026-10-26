"""Dust uv; canonical implementation behind luxcore."""

import bpy

def _ctx(ob, edit=False):
    win = bpy.context.window_manager.windows[0] if bpy.context.window_manager.windows else None
    ov = dict(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])
    if win: ov.update(window=win, screen=win.screen)
    if edit: ov["edit_object"] = ob
    return bpy.context.temp_override(**ov)

def dust_uv(ob, name="DustUV"):
    """Non-overlapping layout for a baked map, beside the tiling UVs. Smart Project is
    deterministic, so a cached map still matches: always call it, even when not re-baking
    (a missing layer makes a LuxCore mapping uvindex -1, which crashes pyluxcore)."""
    me = ob.data
    if me.uv_layers.find(name) >= 0: return
    keep = me.uv_layers.active.name if me.uv_layers.active else None
    me.uv_layers.new(name=name); me.uv_layers.active = me.uv_layers[name]
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    with _ctx(ob): bpy.ops.object.mode_set(mode="EDIT")
    with _ctx(ob, edit=True):
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    if keep: me.uv_layers.active = me.uv_layers[keep]
