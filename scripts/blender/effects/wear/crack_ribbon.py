"""Compact Cycles crack masks from seeded polylines; avoids expanding every segment into SVM."""
import hashlib
import json
import math
import bpy
import numpy as np
import random


def crack_polylines(seed):
    """Return the main unit-arclength polyline and its optional narrower offshoots."""
    rnd = random.Random(seed)
    weights = [rnd.uniform(0.6, 1.7) for _ in range(7)]
    weights = [v / sum(weights) for v in weights]
    angles = [0.0]
    for _ in range(6):
        turn = math.radians(rnd.uniform(20, 40))
        sign = rnd.choice((-1, 1))
        if abs(angles[-1] + sign * turn) > math.radians(50):
            sign = -sign
        angles.append(angles[-1] + sign * turn)
    # Rotate the entire path: kinks keep their20-40degree turns, while the endpoint
    # stays on the assigned overall heading (opening diagonal / edge perpendicular).
    overall = math.atan2(sum(math.sin(a) * w for a, w in zip(angles, weights)),
                         sum(math.cos(a) * w for a, w in zip(angles, weights)))
    angles = [a - overall for a in angles]
    anchors, points = [(0.0, 0.0)], [(0.0, 0.0)]
    slope = last_slope = math.tan(angles[0])
    for i, (angle, length) in enumerate(zip(angles, weights)):
        x, y = anchors[-1]
        end = x + math.cos(angle) * length
        anchors.append((end, y + math.sin(angle) * length))
        if i:
            next_slope = math.tan(angle)
            slope += next_slope - last_slope
            last_slope = next_slope
        px, py = points[-1]
        points.append((end, py + (end - px) * slope))
    phase = rnd.uniform(0, math.tau)
    lines = [(points, 1.0)]
    for chance, lengths, scale in [(.32, (.10, .22), .45), (.38, (.04, .09), .18)]:
        index = rnd.randint(2, 5)
        angle = angles[index] + math.radians(rnd.choice((-1, 1)) * rnd.uniform(45, 75))
        origin = np.array(anchors[index])
        direction = np.array((math.cos(angle), math.sin(angle)))
        length = rnd.uniform(*lengths) if rnd.random() < chance else 0.0
        turn = math.atan(math.tan(math.radians(rnd.choice((-1, 1)) * rnd.uniform(25, 40))))
        if length > 0:
            rotation = np.array(((math.cos(turn), -math.sin(turn)), (math.sin(turn), math.cos(turn))))
            middle = origin + direction * length * .47
            end = middle + rotation @ direction * length * .53
            lines.append(([tuple(origin), tuple(middle), tuple(end)], scale))
    return lines, phase


def _mask_image(seed, length, core, halo):
    # One mask per authored path, cached by its physical parameters. Runtime graphs stay small.
    lines, phase = crack_polylines(seed)
    key = f'{length:.12g}:{core:.12g}:{halo:.12g}:' + json.dumps((lines, phase))
    name = 'Crooked crack ' + hashlib.sha1(key.encode()).hexdigest()[:14]
    if existing := bpy.data.images.get(name):
        return existing
    points = np.array([point for path, _ in lines for point in path])
    padding = halo / length * 1.4
    low = points.min(axis=0) - padding
    high = points.max(axis=0) + padding
    resolution = 1024  # data pixels; the thinnest spurs can remain sub-pixel in the final view
    x = low[0] + (np.arange(resolution, dtype=np.float32) + .5) / resolution * (high[0] - low[0])
    y = low[1] + (np.arange(resolution, dtype=np.float32) + .5) / resolution * (high[1] - low[1])
    xx, yy = np.meshgrid(x, y)
    masks = np.zeros((resolution, resolution, 4), dtype=np.float32)
    for path, scale in lines:
        lengths = [math.dist(a, b) for a, b in zip(path, path[1:])]
        total = sum(lengths)
        offset = 0.0
        for (ax, ay), (bx, by), segment in zip(path, path[1:], lengths):
            dx, dy = bx - ax, by - ay
            t = np.clip(((xx - ax) * dx + (yy - ay) * dy) / segment ** 2, 0, 1)
            distance = np.sqrt((xx - ax - t * dx) ** 2 + (yy - ay - t * dy) ** 2)
            progress = (offset + t * segment) / total
            taper = np.sqrt(np.maximum(0, 1 - progress))
            width = 1 + .25 * np.sin(progress * 27 + phase)  # vary width around its unchanged nominal value
            wc = np.maximum(1e-9, core / length * scale * taper * width)
            wh = halo / length * scale * width
            c = np.clip(1 - distance / wc, 0, 1)
            h = np.clip(1 - distance / wh, 0, 1) * taper
            np.maximum(masks[:, :, 0], c, out=masks[:, :, 0])
            np.maximum(masks[:, :, 1], h, out=masks[:, :, 1])
            offset += segment
    masks[:, :, 3] = 1
    image = bpy.data.images.new(name, width=resolution, height=resolution, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'  # set before pixels: changing it later clears generated data
    image.pixels.foreach_set(masks.ravel())
    image.update()
    image['bounds'] = [float(v) for v in (*low, *high)]
    image['crack_seed'] = seed
    image['main_length'] = length
    image['nominal_core_width'] = core
    image['nominal_halo_width'] = halo
    image['polylines'] = json.dumps(lines)
    image.file_format = 'OPEN_EXR'
    image.pack()  # generated masks must survive saving and reopening the authored scene
    return image


def crooked_ribbon_masks(graph, frame, along, perp, wobble, plane_mask, settings, length_m, y, seed=3, physical_length=None):
    """Sample a seeded crooked polyline mask with fine shader wobble and unchanged nominal widths."""
    length = physical_length if physical_length is not None else length_m
    image = _mask_image(seed, length, settings['core'], settings['halo'])
    low_x, low_y, high_x, high_y = image['bounds']
    def m(op, a, b=0):
        return graph.math(op, a, b, (0, y), frame)
    xx = m('DIVIDE', along, length_m)
    # Pin distortion at the source so opening corners and edges remain attached exactly.
    pin = graph.map_range(xx, 0, .04, (0, y), frame=frame)
    yy = m('DIVIDE', m('ADD', perp, m('MULTIPLY', wobble, pin)), length_m)
    vector = graph.node('ShaderNodeCombineXYZ', (200, y), frame)
    graph.link(m('DIVIDE', m('SUBTRACT', xx, low_x), high_x - low_x), vector.inputs['X'])
    graph.link(m('DIVIDE', m('SUBTRACT', yy, low_y), high_y - low_y), vector.inputs['Y'])
    texture = graph.node('ShaderNodeTexImage', (400, y), frame, label=image.name)
    texture.image = image
    texture.extension = 'CLIP'
    texture.interpolation = 'Linear'
    graph.link(vector.outputs['Vector'], texture.inputs['Vector'])
    separate = graph.node('ShaderNodeSeparateColor', (600, y), frame)
    graph.link(texture.outputs['Color'], separate.inputs['Color'])
    gate = m('MULTIPLY', plane_mask, m('GREATER_THAN', along, -1e-8))
    return m('MULTIPLY', separate.outputs['Red'], gate), m('MULTIPLY', separate.outputs['Green'], gate)
