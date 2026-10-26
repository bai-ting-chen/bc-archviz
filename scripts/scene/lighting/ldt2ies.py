"""Eulumdat (.ldt) -> IES LM-63-2002 (.ies) for Cycles, which reads IES only.

    python ldt2ies.py in.ldt [out.ies]

Keeps the photometry exactly: LDT intensities are cd per 1000 lm of lamp flux and already include
the light output ratio, so the IES gets lamp lumens = total LDT flux, multiplier = flux / 1000.
Both formats are type C with gamma 0 = nadir. Symmetries are written so Cycles needs no guessing:
Isym 1 -> one plane, 2 -> C0..C180, 4 -> C0..C90, 3 (about C90-C270) and 0 -> full C0..C360
(Cycles reads a 90..270 range by shifting it 90 deg, so that layout is never written).
Prints the luminaire lumens integrated from the written candela as a check against the LDT.
"""
import os
import sys

from ldt_read import read_ldt
from ldt_planes import planes
from photometry_integral import lumens
from ies_write import write_ies


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".ies"
    d = read_ldt(src)
    flux, lm = write_ies(d, dst)
    print(f"{d['company']} | {d['name']} | isym {d['isym']}, {len(d['rows'])} planes x {d['ng']} angles")
    print(f"lamp flux {flux:g} lm, LORL {d['lorl']:g} % -> expected {flux * d['lorl'] / 100:.1f} lm; "
          f"integrated from the IES {lm:.1f} lm -> {dst}")
