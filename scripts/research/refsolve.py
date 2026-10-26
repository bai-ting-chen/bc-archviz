"""Camera solve from a repeated element in a reference image (columns, piers, mullions).

Level camera, verticals parallel (shift lens). Inputs per repeat, in reference pixels: centre x,
base y, top y (and optionally the apparent width). The repeats stand on one straight line at a
known pitch. Outputs a façade frame (x along the repeats, repeat 0 at x = 0; y away from the
camera; z up from the base) and the Blender camera for it.

    python refsolve.py readings.json            # print the solve
    from refsolve import Solve                  # then .floor_pt / .plane_pt / .pt_at_z / .fit_circle

readings.json:
    {"W": 2450, "H": 1000, "pitch": 4.5, "f_px": 2700, "cx": 1225,
     "xs": [...], "bases": [...], "tops": [...], "widths": [...],     # widths optional
     "horizon": 715}                                                    # optional override

Method (lighting-camera.md > Camera from a repeated element): base and top lines meet at the
façade vanishing point -> horizon; 1/h steps equal -> equal pitch; pitch fixes scale; eye
height = H * (y_base - horizon) / h. Focal is the weak unknown: estimate it with
`focal_from_sagitta` per round base and confirm in the overlay. The line residual (`residual_m`)
is the check that the readings hold together.
"""
import json
import math
import sys


def _fit_line(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    k = sxy / sxx
    return k, my - k * mx


def focal_from_sagitta(y_base, horizon, sagitta_px, half_width_px):
    """Round base seen from above: depression = asin(sagitta / half-width); f = dy / tan(dep)."""
    dep = math.asin(min(0.999, sagitta_px / half_width_px))
    return (y_base - horizon) / math.tan(dep)


class Solve:
    def __init__(self, xs, bases, tops, pitch, f_px, cx, W, H, widths=None, horizon=None):
        self.F, self.CX, self.W, self.H = float(f_px), float(cx), W, H
        if horizon is None:   # intersect the base and top lines
            kb, cb = _fit_line(xs, bases); kt, ct = _fit_line(xs, tops)
            if abs(kb - kt) < 1e-9:
                raise ValueError("base and top lines are parallel (facade seen head-on): "
                                 "give \"horizon\" in the readings JSON")
            xv = (ct - cb) / (kb - kt)
            horizon = kb * xv + cb
            self.vp = (xv, horizon)
        else:
            self.vp = None
        self.HOR = float(horizon)
        hs = [b - t for b, t in zip(bases, tops)]
        unit = [((x - cx) / h, self.F / h) for x, h in zip(xs, hs)]      # camera plan at height 1
        d = sum(math.dist(unit[i], unit[i + 1]) for i in range(len(unit) - 1)) / (len(unit) - 1)
        self.height = pitch / d                                            # real repeat height
        self.pts = [(u * self.height, v * self.height) for u, v in unit]
        self.eye = self.height * sum((b - self.HOR) / h for b, h in zip(bases, hs)) / len(hs)
        self.width = self.height * sum(w / h for w, h in zip(widths, hs)) / len(hs) if widths else None
        (x0, z0), (x1, z1) = self.pts[0], self.pts[-1]
        n = math.hypot(x1 - x0, z1 - z0)
        self.u = ((x1 - x0) / n, (z1 - z0) / n)                            # along the repeats
        nx, nz = -self.u[1], self.u[0]
        self.n = (nx, nz) if nz > 0 else (-nx, -nz)                        # away from the camera
        self.pitch = pitch
        self.cam = self.to_f(0.0, 0.0)
        self.facade = [self.to_f(*p) for p in self.pts]
        self.residual_m = max(abs(fy) for fx, fy in self.facade)

    # camera plan (X right, Z forward) -> façade frame (x along, y inward), anchored on repeat 0
    def to_f(self, X, Z):
        vx, vz = X - self.pts[0][0], Z - self.pts[0][1]
        return (vx * self.u[0] + vz * self.u[1], vx * self.n[0] + vz * self.n[1])

    def floor_pt(self, x, y, z=0.0):
        """Image pixel of a point at height z (default the floor) -> façade (x, y)."""
        Z = self.F * (self.eye - z) / (y - self.HOR)
        return self.to_f((x - self.CX) * Z / self.F, Z)

    def pt_at_z(self, x, y, z):
        Z = self.F * (z - self.eye) / (self.HOR - y)
        return self.to_f((x - self.CX) * Z / self.F, Z)

    def plane_pt(self, x, y, yf):
        """Image pixel on the vertical plane y = yf of the façade frame -> (x, z)."""
        dx, dz = (x - self.CX) / self.F, 1.0
        a = dx * self.u[0] + dz * self.u[1]; b = dx * self.n[0] + dz * self.n[1]
        t = (yf - self.cam[1]) / b
        return self.cam[0] + t * a, self.eye + t * (self.HOR - y) / self.F

    @staticmethod
    def fit_circle(points):
        """Least-squares circle (cx, cy, r) through plan points — constrain it by including the
        point where the curve visibly meets its neighbour (a free fit can land in front of it)."""
        import numpy as np
        P = np.asarray(points, float)
        A = np.c_[2 * P, np.ones(len(P))]
        c = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
        return float(c[0]), float(c[1]), float(math.sqrt(c[2] + c[0] ** 2 + c[1] ** 2))

    def blender(self, sensor_mm=36.0):
        """Camera for the façade frame: location, rotation (XYZ euler, rad), lens, shifts
        (sensor_fit HORIZONTAL: shifts are fractions of the frame WIDTH)."""
        view = (self.u[1], self.n[1])          # camera +Z (forward) in the façade frame
        yaw = math.atan2(-view[0], view[1])
        return {"location": (self.cam[0], self.cam[1], self.eye), "rotation": (math.pi / 2, 0.0, yaw),
                "lens_mm": self.F / self.W * sensor_mm, "sensor_mm": sensor_mm,
                "shift_x": -(self.CX - self.W / 2) / self.W, "shift_y": (self.HOR - self.H / 2) / self.W}

    def report(self):
        b = self.blender()
        return {"horizon_y": round(self.HOR, 1), "repeat_height_m": round(self.height, 3),
                "eye_m": round(self.eye, 3), "width_m": self.width and round(self.width, 3),
                "residual_m": round(self.residual_m, 3),
                "repeats": [tuple(round(v, 2) for v in p) for p in self.facade],
                "camera": {k: (tuple(round(x, 4) for x in v) if isinstance(v, tuple) else round(v, 4))
                           for k, v in b.items()},
                "yaw_deg": round(math.degrees(b["rotation"][2]), 2)}


def from_json(path):
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    return Solve(r["xs"], r["bases"], r["tops"], r["pitch"], r["f_px"], r.get("cx", r["W"] / 2), r["W"], r["H"],
                 widths=r.get("widths"), horizon=r.get("horizon"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps(from_json(sys.argv[1]).report(), indent=2))
