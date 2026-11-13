"""Two-metal scratch control in the reflection of a narrow bright area light."""


def scratch_fixture(project, samples, kind, settings):
    """Reuse the surface rig, framing two metal panels against a grazing reflection strip."""
    import bpy
    from dataclasses import replace
    import surface_wear_lab as lab
    from mathutils import Vector
    settings = replace(settings, scratch_width_m=2 * 3.9 / lab.FRAME_PIXELS[0])
    sc, materials, _ = lab._fixture(project, samples, kind, settings)
    bpy.data.objects['concrete-wall'].hide_render = True
    sc.camera.location = (-.95, -4, 5)
    aim = Vector((-.95, 0, 0))
    sc.camera.rotation_euler = (aim - sc.camera.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera.data.ortho_scale = 3.9
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .15
    for light in bpy.data.lights:
        if light.type == 'SUN':
            light.energy = 0
    strip = bpy.data.objects['wear-softbox']
    strip.location = (-.95, -4, -5)
    strip.rotation_euler = (aim - strip.location).to_track_quat('-Z', 'Y').to_euler()
    strip.data.shape = 'RECTANGLE'
    strip.data.size, strip.data.size_y = 5.5, .25
    strip.data.energy = 25
    bpy.context.view_layer.update()
    regions = {}
    for i, name in enumerate(lab.SURFACES[:2]):
        x = (i - 1) * 1.9
        regions[name] = lab.surface_region(sc, sc.camera, x)
    return sc, materials[:2], regions


def measure_glints(out, key, field, regions):
    """Measure bright scratch changes on active pixels against the repeated-baseline noise."""
    import numpy as np
    import OpenImageIO as oiio
    def pixels(name):
        return oiio.ImageBuf(str(out / (name + '.png'))).get_pixels()[..., :3]
    off = pixels('off')
    image = pixels(key)
    noise = abs(pixels('procedural') - pixels('noise-floor'))
    results = {}
    for name, (x0, y0, x1, y1) in regions.items():
        active = field[y0:y1, x0:x1] > .05
        delta = image[y0:y1, x0:x1] - off[y0:y1, x0:x1]
        bright = np.maximum(delta.mean(axis=-1), 0)
        floor = float(noise[y0:y1, x0:x1][active].mean())
        gain = float(bright[active].mean())
        results[name] = dict(active_pixels=int(active.sum()), glint_pixels=int(np.sum(active & (bright > 1 / 255))),
            positive_png_mae=gain, local_noise_png_mae=floor, positive_signal_over_noise=gain / max(floor, 1e-12),
            maximum_brightening_codes=float(bright.max() * 255),
            baseline_clipped_fraction=float(np.mean(np.max(off[y0:y1, x0:x1], axis=-1) >= 1)))
        assert results[name]['glint_pixels'] > 20 and gain > floor, (key, name, results[name])
        assert results[name]['baseline_clipped_fraction'] < .01
    return results
