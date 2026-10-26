"""Foot crowns; implementation for water.foot."""
import numpy as np
from materials.water.foot_config import EMPTY_MESH


def crowns(pts, strength, p):
    """Clear crowns at the strongest impacts: tilted rings with spiky rims. (V, F); use thin-wall water."""
    rng = np.random.default_rng(p.seed + 1)
    segments = 14
    angle = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    verts, faces, base = [], [], 0
    for i in np.argsort(-strength)[:int(len(strength) * p.crowns)]:
        centre, s = pts[i], strength[i]
        radius = rng.uniform(.006, .02) * (.7 + .5 * s)
        height = rng.uniform(.003, .014) * s
        tilt = rng.normal(0, .3, 2)
        spikes = 1 + .6 * rng.random(segments) ** 2
        rings = [(radius * .8, -.002), (radius, height * .5), (radius * 1.15, height), (radius * 1.05, height * .2)]
        for ring, (r, z) in enumerate(rings):
            z = z * (spikes if ring == 2 else 1)                        # the rim ring is spiky
            dx, dy = r * np.cos(angle), r * np.sin(angle)
            verts.append(np.c_[centre[0] + dx, centre[1] + dy, centre[2] + z + tilt[0] * dx + tilt[1] * dy])
        for ring in range(3):
            for j in range(segments):
                a0 = base + ring * segments + j
                a1 = base + ring * segments + (j + 1) % segments
                faces.append([a0, a1, a1 + segments, a0 + segments])
        base += 4 * segments
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH
