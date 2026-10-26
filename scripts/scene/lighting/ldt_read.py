"""Read Eulumdat records without changing photometric values."""
import os


def read_ldt(path):
    """Decode an Eulumdat file with its original lamp and intensity values."""
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
