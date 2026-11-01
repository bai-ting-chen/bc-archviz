"""Shared daylight scene, boxes and native-pixel boards for edge controls."""
import json


def scene_setup(archviz, project, samples, location, aim, scale, track=False):
    """Create the fixed daylight scene; keep each control's camera unchanged."""
    import bpy
    from mathutils import Vector
    archviz.set_project(str(project))
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    archviz.render_setup(1100, 1000, samples=samples)
    archviz.use_gpu()
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    world = bpy.data.worlds.new('Control plain sky')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.82, 1.0, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5
    sc.world = world
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 2.0
    sun.angle = 0.12
    light = bpy.data.objects.new('Sun', sun)
    sc.collection.objects.link(light)
    light.rotation_euler = (0.45, -0.5, -0.4)
    cam = bpy.data.objects.new('Fixed camera', bpy.data.cameras.new('Fixed camera'))
    sc.collection.objects.link(cam)
    cam.location = location
    if track:
        target = bpy.data.objects.new('Camera target', None)
        sc.collection.objects.link(target)
        target.location = aim
        constraint = cam.constraints.new('TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
    else:
        cam.rotation_euler = (Vector(aim) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = scale
    sc.camera = cam
    return sc, cam


def box(name, location, dimensions):
    """Create a unit box and apply its requested dimensions."""
    import bpy
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.view_layer.update()
    return ob


def board_views(out, images, columns, keys, text_offset):
    """Write labelled native full/close boards and yield crops plus display arrays."""
    import numpy as np
    from PIL import Image, ImageDraw
    meta = json.loads((out / 'regions.json').read_text())
    for view, crop in [('full', (0, 0, *images['all-on'].size)), ('close', tuple(meta['crop']))]:
        panels = {key: im.crop(crop) for key, im in images.items()}
        arrays = {key: np.asarray(im, dtype=float) / 255 for key, im in panels.items()}
        w, h = panels['all-on'].size
        rows = (len(keys) + columns - 1) // columns
        board = Image.new('RGB', (w * columns, (h + 30) * rows), '#202020')
        draw = ImageDraw.Draw(board)
        for i, key in enumerate(keys):
            x, y = i % columns * w, i // columns * (h + 30)
            board.paste(panels[key], (x, y + 30))
            draw.text((x + text_offset, y + 8), view + ' | ' + key, fill='white')
        board.save(out / ('board-' + view + '.png'))
        yield view, crop, arrays
