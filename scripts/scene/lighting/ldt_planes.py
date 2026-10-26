"""Expand LDT symmetry into Cycles-compatible IES planes."""



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
