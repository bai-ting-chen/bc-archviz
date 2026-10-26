"""Write an LM-63-2002 profile from decoded LDT data."""
from ldt_planes import planes
from photometry_integral import lumens


def write_ies(d, out):
    """Write decoded LDT photometry as IES and return lamp and integrated flux."""
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
