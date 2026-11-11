"""Directional blur control: blender -b --factory-startup --python anisotropy_lab.py -- --out DIR --case glass|metal|glass-bsdf|metallic."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import bpy
import numpy as np
import OpenImageIO as oiio

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SCRIPTS / 'blender'), str(SCRIPTS / 'controls')]
from _scene import black_scene, ortho_camera
from core.archviz import directional_uv
from effects.anisotropy import anisotropy
from materials.shared.dielectric import dielectric


def _box(name, center, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def _emission(name, value):
    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    tree.nodes.clear()
    node = tree.nodes.new('ShaderNodeEmission')
    node.inputs['Color'].default_value = (value, value, value, 1)
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(node.outputs[0], out.inputs['Surface'])
    return mat


def _single_bsdf(name, node_type, roughness):
    """A material whose surface is one BSDF node of the given type."""
    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    tree.nodes.clear()
    node = tree.nodes.new(node_type)
    node.inputs['Roughness'].default_value = roughness
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(node.outputs[0], out.inputs['Surface'])
    return mat, node


# Blur axis that widens at rotation 0 with the tangent along X (anisotropy.md step 3).
BROAD_AXIS = {'glass': 'x', 'metal': 'x', 'glass-bsdf': 'y', 'metallic': 'x'}


def _grid(reflection):
    # Reuse the backlit grid on either side of the surface for transmission/reflection.
    # Metres: 0.20 setback, 0.12-wide lines; stagger the layers to avoid coincident faces.
    white = _emission('backlit-white', 1)
    black = _emission('grid-black', .002)
    side = 1 if reflection else -1
    objects = [_box('backlight', (0, 0, side * .20), (2, 2, .002), white)]
    for i, position in enumerate([-.4, 0, .4]):
        objects.append(_box('grid-vertical-' + str(i), (position, 0, side * .197),
                            (.12, 2, .002), black))
        objects.append(_box('grid-horizontal-' + str(i), (0, position, side * .194),
                            (2, .12, .002), black))
    if reflection:
        for obj in objects:
            obj.visible_camera = False


def _scene(case, variant, samples):
    # Measurement windows below refer to this 768 px frame and 1.15 m orthographic span.
    sc = black_scene(samples=samples, res=768)
    sc.cycles.max_bounces = 16
    sc.cycles.transmission_bounces = 12
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    ortho_camera(3, 1.15)
    reflective = case in ('metal', 'metallic')
    _grid(reflective)
    amount = 0.0 if variant.startswith('off') else .8
    rotation = .25 if variant == 'rotated' else 0.0  # turns; quarter turn = 90 degrees
    if case == 'glass':
        mat = dielectric('rough-glass', roughness=.24, anisotropy=amount,
                         rotation=rotation, tangent=(1, 0, 0))
    elif case == 'glass-bsdf':
        mat, node = _single_bsdf('rough-glass-bsdf', 'ShaderNodeBsdfGlass', .24)
        anisotropy(node, amount, rotation, (1, 0, 0))
    else:
        if case == 'metal':
            mat = bpy.data.materials.new('rough-metal')
            node = mat.node_tree.nodes.get('Principled BSDF')
            node.inputs['Metallic'].default_value = 1
        else:
            mat, node = _single_bsdf('rough-metallic-bsdf', 'ShaderNodeBsdfMetallic', .12)
        node.inputs['Base Color'].default_value = (.67, .64, .60, 1)
        node.inputs['Roughness'].default_value = .12
        # Exercise the UV path as well as the glass controls' explicit world axis.
        anisotropy(node, amount, rotation, 'directional-uv')
    pane = _box(case + '-plate', (0, 0, 0), (1, 1, .01), mat)
    if reflective:
        directional_uv(pane, 1, name='directional-uv', axis='X')
    sc.cycles.seed = 41 if variant == 'off-repeat' else 17
    return sc


def _crossing(profile, level):
    # Central rising grid edge; same window and interpolation as the transmission control.
    for i in range(392, 490):
        if profile[i] <= level < profile[i + 1]:
            return i + (level - profile[i]) / (profile[i + 1] - profile[i])
    raise ValueError('Grid edge has no 10/90 percent crossing')


def _blur_width(image, axis):
    grey = image.mean(axis=-1)
    profile = grey[180:300].mean(axis=0) if axis == 'x' else grey[:, 180:300].mean(axis=1)
    black = profile[376:392].mean()
    white = profile[490:510].mean()
    normalized = (profile - black) / (white - black)
    return float(_crossing(normalized, .9) - _crossing(normalized, .1))


def _read(path):
    reader = oiio.ImageInput.open(str(path))
    pixels = np.asarray(reader.read_image(format=oiio.UINT8)).copy() / 255.0
    reader.close()
    return pixels


def _write(path, pixels):
    pixels = np.ascontiguousarray(np.clip(pixels * 255, 0, 255).astype(np.uint8))
    writer = oiio.ImageOutput.create(str(path))
    writer.open(str(path), oiio.ImageSpec(pixels.shape[1], pixels.shape[0], 3, oiio.UINT8))
    writer.write_image(pixels)
    writer.close()


def _measure(out, prefix):
    images = {v: _read(out / (prefix + '-' + v + '.png'))
              for v in ['off', 'on', 'rotated', 'off-repeat']}
    widths = {v: {axis: _blur_width(im, axis) for axis in ['x', 'y']}
              for v, im in images.items()}
    noise_width = max(abs(widths['off'][a] - widths['off-repeat'][a]) for a in ['x', 'y'])
    separation = [abs(widths[v]['x'] - widths[v]['y']) for v in ['on', 'rotated']]
    swapped = ((widths['on']['x'] - widths['on']['y']) *
               (widths['rotated']['x'] - widths['rotated']['y']) < 0)
    def roi(im):
        return np.concatenate([im[180:300, 392:490].reshape(-1, 3),
                               im[392:490, 180:300].reshape(-1, 3)])
    noise = float(np.abs(roi(images['off']) - roi(images['off-repeat'])).mean())
    feature = float(np.abs(roi(images['off']) - roi(images['on'])).mean())
    broad_axis = max('xy', key=lambda a: widths['on'][a])
    result = dict(widths_px=widths, broad_axis=broad_axis, noise_width_px=noise_width,
                  noise_mae_percent=noise * 100, feature_mae_percent=feature * 100,
                  swaps=swapped, passes=swapped and min(separation) > noise_width and feature > noise)
    # Native crops in order off / on / rotated; resolution stays below 1280 px.
    _write(out / (prefix + '-pair.png'), np.concatenate(
        [images[v][175:590, 175:590] for v in ['off', 'on', 'rotated']], axis=1))
    _write(out / (prefix + '-feature-diff.png'), np.abs(images['on'] - images['off']) * 4)
    _write(out / (prefix + '-noise-diff.png'), np.abs(images['off-repeat'] - images['off']) * 4)
    return result


def main():
    """Render off/on/quarter-turn/repeated-off and measure display-PNG edge widths."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=sorted(BROAD_AXIS), required=True)
    parser.add_argument('--samples', type=int, default=1024)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    args.out.mkdir(parents=True, exist_ok=True)
    prefix = args.case + '-' + '.'.join(map(str, bpy.app.version[:2]))
    metadata = []
    for variant in ['off', 'on', 'rotated', 'off-repeat']:
        vram = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.free,memory.used',
                                        '--format=csv'], text=True)
        print('VRAM BEFORE GPU RENDER\n' + vram, flush=True)
        sc = _scene(args.case, variant, args.samples)
        sc.render.filepath = str(args.out / (prefix + '-' + variant + '.png'))
        bpy.ops.render.render(write_still=True)
        metadata.append(dict(variant=variant, seed=sc.cycles.seed, samples=sc.cycles.samples,
                             device=sc.cycles.device, vram=vram))
    result = _measure(args.out, prefix)
    result.update(version=bpy.app.version_string, case=args.case, renders=metadata)
    (args.out / (prefix + '-measurements.json')).write_text(json.dumps(result, indent=2))
    print('ANISOTROPY_RESULT', json.dumps(result), flush=True)
    assert result['passes'], 'Directional blur failed noise-floor or rotation check'
    assert result['broad_axis'] == BROAD_AXIS[args.case], 'Broad blur axis differs from anisotropy.md step 3'


if __name__ == '__main__':
    main()
