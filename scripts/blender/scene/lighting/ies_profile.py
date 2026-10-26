"""Ies profile; implementation for interior."""
import math


def ies_read(path):
    """Parse an LM-63 type C file. Returns header lumens, integrated luminaire lumens, peak cd,
    beam (50 % of peak) and field (10 %) full angles in degrees, and the [MANUFAC]/[LUMCAT] tags."""
    with open(path, errors="replace") as f:
        txt = f.read()
    head, _, rest = txt.partition("TILT=")
    tags = {}
    for line in head.splitlines():
        if line.startswith("[") and "]" in line:
            k, v = line[1:].split("]", 1)
            tags.setdefault(k.strip(), v.strip())
    tok = rest.split()
    tilt = tok.pop(0)
    if tilt == "INCLUDE":
        tok.pop(0); n = int(tok.pop(0)); del tok[:2 * n]
    nums = [float(t) for t in tok]
    lamps, lm_lamp, mult, nv, nh, ptype = nums[0], nums[1], nums[2], int(nums[3]), int(nums[4]), int(nums[5])
    ballast, blp = nums[10], nums[11]
    if ptype != 1:
        raise ValueError(f"{path}: photometric type {ptype}, only type C is handled")
    i = 13
    va, ha = nums[i:i + nv], nums[i + nv:i + nv + nh]
    i += nv + nh
    k = mult * ballast * blp
    cd = [[k * c for c in nums[i + h * nv:i + (h + 1) * nv]] for h in range(nh)]
    # flux = sum over C planes of  integral I(theta) sin(theta) dtheta, weighted by each plane's share of 2pi
    def plane_flux(row):
        return sum((row[j] * math.sin(math.radians(va[j])) + row[j + 1] * math.sin(math.radians(va[j + 1])))
                   / 2 * math.radians(va[j + 1] - va[j]) for j in range(nv - 1))
    if nh == 1:
        flux = 2 * math.pi * plane_flux(cd[0])
    else:
        span = ha[-1] - ha[0]
        flux = sum((plane_flux(cd[h]) + plane_flux(cd[h + 1])) / 2 * math.radians(ha[h + 1] - ha[h])
                   for h in range(nh - 1)) * 360.0 / span
    mean = [sum(cd[h][j] for h in range(nh)) / nh for j in range(nv)]   # plane-averaged profile
    peak = max(max(r) for r in cd)

    def cut(frac):
        for j in range(1, nv):
            if mean[j] < frac * mean[0] <= mean[j - 1]:
                t = (mean[j - 1] - frac * mean[0]) / (mean[j - 1] - mean[j])
                return 2 * (va[j - 1] + t * (va[j] - va[j - 1]))
        return None
    return {"lumens_header": lamps * lm_lamp if lm_lamp > 0 else None, "absolute": lm_lamp < 0,
            "lumens": flux, "peak_cd": peak, "beam_deg": cut(0.5), "field_deg": cut(0.1),
            "manufacturer": tags.get("MANUFAC"), "catalog": tags.get("LUMCAT"),
            "luminaire": tags.get("LUMINAIRE"), "lamp": tags.get("LAMP")}
