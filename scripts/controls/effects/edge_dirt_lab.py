"""Fixed-camera line/dust ablations; run in headless Blender, then host --analyze OUT."""
import argparse
import json
from pathlib import Path
import sys
from edge_lab_common import scene_setup, box, board_views

VARIANTS = [('all-on', True, True, 43), ('line-off', False, True, 43),
            ('dust-off', True, False, 43), ('both-off', False, False, 43),
            ('noise-floor', False, False, 79)]


def analyze(out):
    """Write native-pixel full/crop boards and display-PNG edge-band differences."""
    import numpy as np
    from PIL import Image, ImageDraw
    meta = json.loads((out / 'regions.json').read_text())
    images = {key: Image.open(out / (key + '.png')).convert('RGB') for key, *_ in VARIANTS}
    stats = {}
    for view, crop, arrays in board_views(out, images, 2, [key for key, *_ in VARIANTS[:4]], 12):
        stats[view] = {}
        for kind, polys in meta['bands'].items():
            mask = Image.new('L', images['all-on'].size)
            md = ImageDraw.Draw(mask)
            for poly in polys:
                md.polygon([tuple(p) for p in poly], fill=255)
            region = np.asarray(mask.crop(crop)) > 0
            assert region.sum() > 20, (view, kind, region.sum())
            base = arrays['both-off']
            noise = float(np.abs(arrays['noise-floor'] - base)[region].mean())
            row = {'pixels': int(region.sum()), 'noise_floor': noise}
            for key, *_ in VARIANTS[:4]:
                row[key] = float(np.abs(arrays[key] - base)[region].mean())
            stats[view][kind] = row
            print(view, kind, json.dumps(row), flush=True)
        # Display-space differences are evidence only; measurements use the source PNGs.
        for key in ('all-on', 'line-off', 'dust-off'):
            diff = np.clip(np.abs(arrays[key] - arrays['both-off']) * 6 * 255, 0, 255).astype('uint8')
            Image.fromarray(diff).save(out / (view + '-' + key + '-diff-x6.png'))
    (out / 'measurements.json').write_text(json.dumps(stats, indent=2))
    for view, kinds in stats.items():
        for kind, row in kinds.items():
            if kind == 'convex':
                # Full-board visibility must survive the repeated-baseline noise floor.
                if view == 'full':
                    assert row['dust-off'] > max(0.02, 3 * row['noise_floor']), (view, kind, 'line', row)
                continue
            assert row['line-off'] > row['noise_floor'], (view, kind, 'dust', row)
            if kind == 'concave':
                # The reference calls for almost no inside line: it need not exceed noise.
                assert row['dust-off'] < row['noise_floor'] + 0.25 * row['line-off'], (view, kind, row)
    print('EDGE_DIRT_CONTROL_PASS', flush=True)


def build_and_render(out, project, samples):
    """Render the outside field and AO corner masks on separate meeting objects."""
    import bpy
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender'))
    import core.archviz as archviz
    from effects.wear.dirt import LINE_AMOUNT, DUST_AMOUNT
    sc, cam = scene_setup(archviz, project, samples, (3.3, -5.5, 3.1), (0.1, 0.35, 1.0), 3.6, track=True)
    mats = _specimens(archviz)
    _write_regions(out, samples, sc, cam)
    for key, line_on, dust_on, seed in VARIANTS:
        for mat in mats:
            for node in mat.node_tree.nodes:
                if node.label == 'Edge line strength':
                    node.inputs[1].default_value = LINE_AMOUNT if line_on else 0
                if node.label == 'Edge dust strength':
                    node.inputs[1].default_value = DUST_AMOUNT if dust_on else 0
        sc.cycles.seed = seed
        archviz.render_to(str(out / (key + '.png')))
        print('RENDER_COMPLETE', key, flush=True)


def _material_box(archviz, name, location, dimensions, mat, field=False):
    import bmesh
    import bpy
    from mathutils import Vector
    ob = box(name, location, dimensions)
    if field:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=100, use_grid_fill=True)
        bm.to_mesh(ob.data)
        bm.free()
        d = ob.data.attributes.new('edge_dist', 'FLOAT', 'POINT')
        vertex_d = ob.data.attributes.new('edge_vertex_dist', 'FLOAT', 'POINT')
        vertex_valid = ob.data.attributes.new('edge_vertex_valid', 'FLOAT', 'POINT')
        rest = ob.data.attributes.new('rest_pos', 'FLOAT_VECTOR', 'POINT')
        for i, v in enumerate(ob.data.vertices):
            # Clean box surface distance: one boundary gap is zero; next is the edge distance.
            gaps = sorted(dimensions[j] / 2 - abs(v.co[j]) for j in range(3))
            d.data[i].value = max(0, gaps[1])
            vertex_d.data[i].value = sum(max(0, q) ** 2 for q in gaps) ** 0.5
            vertex_valid.data[i].value = 1.0
            rest.data[i].vector = v.co + Vector(location)
    bpy.context.view_layer.update()
    archviz.box_uv(ob, size=2.0)
    ob.data.materials.append(mat)
    return ob



def _specimens(archviz):
    import bpy
    from materials.concrete.concrete import concrete_study
    from effects.wear import weathered_concrete, add_corner_dirt
    mats = []
    column = weathered_concrete()
    add_corner_dirt(column)
    _material_box(archviz, 'Concrete column', (-0.35, 0.35, 1.1), (0.6, 0.6, 2.2), column, field=True)
    mats.append(column)
    for name, pos, dims in [('Floor', (0, -0.5, -0.1), (5, 5, 0.2)),
                             ('Wall', (0, 0.75, 1.5), (5, 0.2, 3))]:
        mat = concrete_study(name=name, edge_dark=False, bevel_chips=False)
        add_corner_dirt(mat)
        mats.append(mat)
        _material_box(archviz, name, pos, dims, mat)
    bpy.context.view_layer.update()

    return mats


def _write_regions(out, samples, sc, cam):
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    def pixel(p):
        q = world_to_camera_view(sc, cam, Vector(p))
        assert q.z > 0
        return [round(q.x * 1100), round((1 - q.y) * 1000)]

    convex = [[(-0.05, 0.05, 0.15), (-0.09, 0.05, 0.15),
               (-0.09, 0.05, 1.9), (-0.05, 0.05, 1.9)],
              [(-0.05, 0.05, 0.15), (-0.05, 0.09, 0.15),
               (-0.05, 0.09, 1.9), (-0.05, 0.05, 1.9)]]
    concave = [[(0.2, 0.65, 0.001), (1.0, 0.65, 0.001),
                (1.0, 0.61, 0.001), (0.2, 0.61, 0.001)],
               [(0.2, 0.649, 0.001), (1.0, 0.649, 0.001),
                (1.0, 0.649, 0.04), (0.2, 0.649, 0.04)]]
    bands = {k: [[pixel(p) for p in poly] for poly in polys]
             for k, polys in [('convex', convex), ('concave', concave)]}
    # Native crop of the fixed full frame, containing edge and floor/wall contact.
    crop = [350, 470, 900, 900]
    (out / 'regions.json').write_text(json.dumps({'bands': bands, 'crop': crop,
          'samples': samples, 'mm_per_pixel_at_orthographic_plane': 3600 / 1100}, indent=2))


def main():
    """Headless render command, or host-side analysis without importing Blender."""
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--samples', type=int, default=128)
    parser.add_argument('--analyze', action='store_true')
    opts = parser.parse_args(args)
    opts.out.mkdir(parents=True, exist_ok=True)
    if opts.analyze:
        analyze(opts.out)
    else:
        if opts.project is None:
            parser.error('--project is required for the concrete maps')
        build_and_render(opts.out, opts.project, opts.samples)


if __name__ == '__main__':
    main()
