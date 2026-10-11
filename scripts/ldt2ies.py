"""Eulumdat (.ldt) -> IES LM-63-2002 (.ies) for Cycles, which reads IES only.

    python ldt2ies.py in.ldt [out.ies]

Keeps the photometry exactly: LDT intensities are cd per 1000 lm of lamp flux and already include
the light output ratio, so the IES gets lamp lumens = total LDT flux, multiplier = flux / 1000.
Both formats are type C with gamma 0 = nadir. Symmetries are written so Cycles needs no guessing:
Isym 1 -> one plane, 2 -> C0..C180, 4 -> C0..C90, 3 (about C90-C270) and 0 -> full C0..C360
(Cycles reads a 90..270 range by shifting it 90 deg, so that layout is never written).
Prints the luminaire lumens integrated from the written candela as a check against the LDT.
"""
import math
import os
import sys


def read_ldt(path):
    with open(path, "rb") as f:
        raw = f.read()
    raw = raw[3:] if raw[:3] == bytes((0xEF, 0xBB, 0xBF)) else raw
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1")
    L = [ln.strip() for ln in txt.splitlines()]
    num = lambda i: float(L[i].replace(",", "."))
    d = {"company": L[0], "isym": int(num(2)), "mc": int(num(3)), "dc": num(4), "ng": int(num(5)),
         "dg": num(6), "report": L[7], "name": L[8], "number": L[9], "date": L[11],
         "length_mm": num(12), "width_mm": num(13), "height_mm": num(14),
         "lum_length_mm": num(15), "lum_width_mm": num(16), "dff": num(21), "lorl": num(22),
         "conv": num(23), "tilt": num(24)}
    n = int(num(25))
    i = 26
    sets = []
    for _ in range(n):
        sets.append({"count": num(i), "type": L[i + n], "flux": num(i + 2 * n), "cct": L[i + 3 * n],
                     "cri": L[i + 4 * n], "watts": num(i + 5 * n)})
        i += 1
    i = 26 + 6 * n + 10                                   # skip the 10 direct ratios
    vals = []
    for ln in L[i:]:
        vals += [float(t.replace(",", ".")) for t in ln.split()]
    mc, ng = d["mc"], d["ng"]
    c = vals[:mc]
    g = vals[mc:mc + ng]
    cd = vals[mc + ng:]
    nplanes = {0: mc, 1: 1, 2: mc // 2 + 1, 3: mc // 2 + 1, 4: mc // 4 + 1}[d["isym"]]
    rows = [cd[p * ng:(p + 1) * ng] for p in range(nplanes)]
    if len(cd) < nplanes * ng:
        raise ValueError(f"{path}: {len(cd)} intensities, expected {nplanes * ng}")
    d.update(sets=sets, c=c, g=g, rows=rows, src=os.path.basename(path))
    return d


def planes(d):
    """(h_angles, rows) in the layout written to the IES file."""
    isym, c, rows = d["isym"], d["c"], d["rows"]
    if isym == 1:
        return [0.0], rows[:1]
    if isym == 2:                                         # stored C0..C180
        return c[:len(rows)], rows
    if isym == 4:                                         # stored C0..C90
        return c[:len(rows)], rows
    if isym == 3:                                         # stored C90..C270; mirror: I(C) = I(180 - C)
        dc = d["dc"]
        stored = {round(90.0 + k * dc, 6): r for k, r in enumerate(rows)}
        hs = [k * dc for k in range(int(round(360 / dc)) + 1)]
        return hs, [stored[round(h if 90 <= h <= 270 else (180.0 - h) % 360, 6)] for h in hs]
    hs = list(c) + [360.0]                                # isym 0: all planes, close the circle
    return hs, rows + [rows[0]]


def lumens(v, h, rows):
    def plane(r):
        return sum((r[j] * math.sin(math.radians(v[j])) + r[j + 1] * math.sin(math.radians(v[j + 1])))
                   / 2 * math.radians(v[j + 1] - v[j]) for j in range(len(v) - 1))
    if len(h) == 1:
        return 2 * math.pi * plane(rows[0])
    return sum((plane(rows[k]) + plane(rows[k + 1])) / 2 * math.radians(h[k + 1] - h[k])
               for k in range(len(h) - 1)) * 360.0 / (h[-1] - h[0])


def write_ies(d, out):
    flux = sum(s["flux"] for s in d["sets"])              # 26c is the total flux of each lamp set
    s0 = d["sets"][0]
    h, rows = planes(d)
    circ = d["width_mm"] == 0
    w = -(d["lum_length_mm"] / 1000) if circ else d["lum_width_mm"] / 1000
    ln = 0.0 if circ else d["lum_length_mm"] / 1000
    lines = ["IESNA:LM-63-2002",
             f"[TEST]{d['report']}", f"[MANUFAC]{d['company']}", f"[LUMCAT]{d['number']}",
             f"[LUMINAIRE]{d['name']}", f"[LAMP]{s0['type']} {s0['cct']}",
             f"[ISSUEDATE]{d['date']}", f"[OTHER]converted from {d['src']} by ldt2ies.py, "
             f"LORL {d['lorl']:g} %", "TILT=NONE",
             f"1 {flux:g} {flux / 1000:g} {len(d['g'])} {len(h)} 1 2 {w:g} {ln:g} 0",
             f"1 1 {sum(s['watts'] for s in d['sets']):g}"]
    lines.append(" ".join(f"{a:g}" for a in d["g"]))
    lines.append(" ".join(f"{a:g}" for a in h))
    lines += [" ".join(f"{x:g}" for x in r) for r in rows]
    with open(out, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(lines) + "\n")
    return flux, lumens(d["g"], h, [[x * flux / 1000 for x in r] for r in rows])


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".ies"
    d = read_ldt(src)
    flux, lm = write_ies(d, dst)
    print(f"{d['company']} | {d['name']} | isym {d['isym']}, {len(d['rows'])} planes x {d['ng']} angles")
    print(f"lamp flux {flux:g} lm, LORL {d['lorl']:g} % -> expected {flux * d['lorl'] / 100:.1f} lm; "
          f"integrated from the IES {lm:.1f} lm -> {dst}")
