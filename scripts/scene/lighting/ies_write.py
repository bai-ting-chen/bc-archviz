"""Write an LM-63-2002 profile from decoded LDT data."""
from ldt_planes import planes
from photometry_integral import lumens


def write_ies(profile, out):
    """Write decoded LDT photometry as IES and return lamp and integrated flux."""
    flux = sum(s["flux"] for s in profile["sets"])              # 26c is the total flux of each lamp set
    s0 = profile["sets"][0]
    h, rows = planes(profile)
    circ = profile["width_mm"] == 0
    w = -(profile["lum_length_mm"] / 1000) if circ else profile["lum_width_mm"] / 1000
    ln = 0.0 if circ else profile["lum_length_mm"] / 1000
    lines = ["IESNA:LM-63-2002",
             f"[TEST]{profile['report']}", f"[MANUFAC]{profile['company']}", f"[LUMCAT]{profile['number']}",
             f"[LUMINAIRE]{profile['name']}", f"[LAMP]{s0['type']} {s0['cct']}",
             f"[ISSUEDATE]{profile['date']}", f"[OTHER]converted from {profile['src']} by ldt_to_ies.py, "
             f"LORL {profile['lorl']:g} %", "TILT=NONE",
             f"1 {flux:g} {flux / 1000:g} {len(profile['g'])} {len(h)} 1 2 {w:g} {ln:g} 0",
             f"1 1 {sum(s['watts'] for s in profile['sets']):g}"]
    lines.append(" ".join(f"{a:g}" for a in profile["g"]))
    lines.append(" ".join(f"{a:g}" for a in h))
    lines += [" ".join(f"{x:g}" for x in r) for r in rows]
    with open(out, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(lines) + "\n")
    return flux, lumens(profile["g"], h, [[x * flux / 1000 for x in r] for r in rows])
