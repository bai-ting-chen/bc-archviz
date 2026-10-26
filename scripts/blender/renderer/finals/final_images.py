"""Final images; implementation for finals."""
import bpy


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
