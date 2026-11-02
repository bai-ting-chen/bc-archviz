"""Full-stack edge-wear ablations; headless Blender renders, host --analyze measures PNGs."""
import argparse
import json
from pathlib import Path
import sys
from edge_lab_common import scene_setup, box, board_views

LAYERS = ('rounded-edge', 'line', 'dust', 'chips', 'run-off', 'opening-cracks', 'edge-cracks')
VARIANTS = ('all-on',) + tuple(k + '-off' for k in LAYERS) + ('noise-floor',)


def analyze(out):
    """Build labelled native-pixel boards and measure each layer against all-on in its band."""
    import numpy as np
    from PIL import Image, ImageDraw
    meta = json.loads((out / 'regions.json').read_text())
    images = {k: Image.open(out / (k + '.png')).convert('RGB') for k in VARIANTS}
    stats = {}
    for view, crop, arrays in board_views(out, images, 3, VARIANTS, 10):
        stats[view] = {}
        for layer in LAYERS:
            mask = Image.new('L', images['all-on'].size)
            painter = ImageDraw.Draw(mask)
            for poly in meta['bands'][layer]:
                painter.polygon([tuple(p) for p in poly], fill=255)
            region = np.asarray(mask.crop(crop)) > 0
            assert region.sum() > 20, (view, layer, region.sum())
            delta = np.abs(arrays[layer + '-off'] - arrays['all-on'])
            noise = np.abs(arrays['noise-floor'] - arrays['all-on'])
            stats[view][layer] = {'pixels': int(region.sum()), 'difference_pct': float(delta[region].mean() * 100),
                                  'noise_pct': float(noise[region].mean() * 100),
                                  'above_noise': bool(delta[region].mean() > noise[region].mean())}
            Image.fromarray(np.clip(delta * 6 * 255, 0, 255).astype('uint8')).save(out / (view + '-' + layer + '-diff-x6.png'))
        print(view, json.dumps(stats[view]), flush=True)
    (out / 'measurements.json').write_text(json.dumps(stats, indent=2))


def render(out, project, samples, only=None):
    """Build the full-stack control and render the selected ablations."""
    import bpy
    import faulthandler
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender'))
    import core.archviz as archviz
    from effects.round_edges import set_round_radius
    faulthandler.dump_traceback_later(60, repeat=True)
    sc, cam = scene_setup(archviz, project, samples, (4, -6, 3.5), (0.45, 0, 1.25), 4.5)
    set_round_radius(0.0025)
    wall, column, floor = _specimens()
    mats, chip_mods, counts = _materials(wall, column, floor, archviz)
    print('BUILD evaluate', flush=True)
    bpy.context.view_layer.update()
    faulthandler.cancel_dump_traceback_later()

    _write_regions(out, samples, sc, cam, wall, column, counts, mats)
    _render_variants(out, only, mats, chip_mods, sc, archviz)


def _specimens():
    import bpy
    # Quad ring: dicing a Boolean's concave n-gons can fan triangles across the opening.
    import bmesh
    ring = [(-0.55, 0), (2.05, 0), (2.05, 2.6), (-0.55, 2.6),
            (0.325, 0.975), (1.175, 0.975), (1.175, 2.025), (0.325, 2.025)]
    vertices = [(x, y, z) for y in (0, 0.3) for x, z in ring]
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.extend([(i, j, j + 4, i + 4), (i + 12, j + 12, j + 8, i + 8),
                      (i, i + 8, j + 8, j), (i + 4, j + 4, j + 12, i + 12)])
    mesh = bpy.data.meshes.new('Window wall quad ring')
    mesh.from_pydata(vertices, [], faces)
    wall = bpy.data.objects.new('Window wall', mesh)
    bpy.context.scene.collection.objects.link(wall)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    coping = box('Coping drip edge', (0.75, 0.11, 2.65), (2.8, 0.52, 0.10))
    # Joined clean geometry lets leak-field upward rays see the actual coping, not a substitute field.
    bpy.ops.object.select_all(action='DESELECT')
    wall.select_set(True)
    coping.select_set(True)
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.join()
    column = box('Chipped column', (-1.05, -0.05, 1.1), (0.55, 0.55, 2.2))
    floor = box('Floor', (0, 0, -0.1), (8, 7, 0.2))
    return wall, column, floor


def _materials(wall, column, floor, archviz):
    import bpy
    from effects.edge_wear import (weathered_concrete, dice, add_edge_wear, edge_wear_group,
                                   add_leak_field, add_runoff, add_cracks, add_edge_cracks,
                                   edge_crack_edges, add_corner_dirt)
    mats, chip_mods = [], []
    counts = {}
    for ob in (wall, column, floor):
        print('BUILD material', ob.name, flush=True)
        edges = edge_crack_edges(ob) if ob != floor else []
        if ob == floor:
            from materials.concrete.concrete import concrete_study
            mat = concrete_study(name='Floor material', edge_dark=False, bevel_chips=False)
        else:
            mat = weathered_concrete(name=ob.name + ' material')
        add_corner_dirt(mat)
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        for face in ob.data.polygons:
            face.material_index = 0
        archviz.box_uv(ob, size=2.0)
        if ob != floor:
            print('BUILD dice', ob.name, flush=True)
            dice(ob, size=0.075)
            group = edge_wear_group(ob.name + ' field', level=2, chips=ob == column)
            mod = add_edge_wear(ob, group)
            if ob == column:
                chip_mods.append(mod)
            if ob == wall:
                add_leak_field(ob)
                add_runoff(mat)
                add_cracks(mat, [('y', 0, 0.325, 1.175, 0.975, 2.025, False)])
            print('BUILD edge cracks', ob.name, len(edges), flush=True)
            add_edge_cracks(mat, edges, seed=17 if ob == wall else 31)
            counts[ob.name] = mat['edge_crack_count']
        mats.append(mat)
    return mats, chip_mods, counts


def _write_regions(out, samples, sc, cam, wall, column, counts, mats):
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    def pixel(p):
        q = world_to_camera_view(sc, cam, Vector(p))
        return [round(q.x * 1100), round((1 - q.y) * 1000)]

    def rectangle(x0, x1, z0, z1, y=-0.001):
        return [pixel((x0, y, z0)), pixel((x1, y, z0)), pixel((x1, y, z1)), pixel((x0, y, z1))]

    edge_band = [rectangle(-0.825, -0.775, 0.12, 2.12, -0.326),
                 [pixel((-0.774, -0.325, 0.12)), pixel((-0.774, -0.275, 0.12)),
                  pixel((-0.774, -0.275, 2.12)), pixel((-0.774, -0.325, 2.12))]]
    wall_edges = [rectangle(-0.55, -0.32, 0.1, 2.5), rectangle(1.8, 2.05, 0.1, 2.5),
                  rectangle(-0.5, 2, 2.35, 2.6)]
    bands = {'rounded-edge': edge_band + [rectangle(-0.6, 2.1, 2.6, 2.62, -0.151)], 'line': edge_band,
             'dust': [rectangle(-0.5, 1.9, 0.002, 0.09)], 'chips': edge_band,
             'run-off': [rectangle(-0.48, 2, 2.1, 2.57)],
             'opening-cracks': [rectangle(-0.05, 0.4, 1.95, 2.45), rectangle(1.1, 1.65, 1.95, 2.45),
                                rectangle(-0.05, 0.4, 0.5, 1.05), rectangle(1.1, 1.65, 0.5, 1.05)],
             'edge-cracks': wall_edges}
    (out / 'regions.json').write_text(json.dumps({'bands': bands, 'crop': [200, 120, 960, 900],
          'samples': samples, 'mm_per_pixel': 4500 / 1100, 'edge_crack_counts': counts,
          'modifier_order': {ob.name: [m.name for m in ob.modifiers] for ob in (wall, column)}}, indent=2))
    from graph_dump import dump_material
    (out / 'full-stack-graphs.json').write_text(json.dumps({m.name: dump_material(m) for m in mats}))


def _render_variants(out, only, mats, chip_mods, sc, archviz):
    import bpy
    from effects.edge_wear import set_input, switch_rounding
    from effects.edge_dirt import LINE_AMOUNT, DUST_AMOUNT
    for key in VARIANTS:
        if only and key not in only:
            continue
        for mat in mats:
            for node in mat.node_tree.nodes:
                if node.label in ('Edge line strength', 'Edge dust strength', 'Chips strength', 'Run-off strength'):
                    kind = {'Edge line strength': 'line', 'Edge dust strength': 'dust',
                            'Chips strength': 'chips', 'Run-off strength': 'run-off'}[node.label]
                    default = LINE_AMOUNT if kind == 'line' else DUST_AMOUNT if kind == 'dust' else 1.0
                    node.inputs[1].default_value = 0 if key == kind + '-off' else default
                if node.label in ('Opening cracks strength', 'Edge cracks strength'):
                    kind = 'opening-cracks' if node.label.startswith('Opening') else 'edge-cracks'
                    node.outputs[0].default_value = 0 if key == kind + '-off' else 1
        for mat in mats:
            switch_rounding(mat, rounded_edges=key != 'rounded-edge-off')
        for mod in chip_mods:
            set_input(mod, 'Chip Depth', 0 if key == 'chips-off' else 0.018)
            mod.id_data.update_tag()
        sc.cycles.seed = 79 if key == 'noise-floor' else 43
        bpy.context.view_layer.update()
        archviz.render_to(str(out / (key + '.png')))
        print('RENDER_COMPLETE', key, flush=True)


def main():
    """Render ablations or analyze their saved display PNGs."""
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--samples', type=int, default=256)
    parser.add_argument('--analyze', action='store_true')
    parser.add_argument('--only', nargs='+', choices=VARIANTS)
    opts = parser.parse_args(args)
    opts.out.mkdir(parents=True, exist_ok=True)
    if opts.analyze:
        analyze(opts.out)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        render(opts.out, opts.project, opts.samples, opts.only)


if __name__ == '__main__':
    main()
