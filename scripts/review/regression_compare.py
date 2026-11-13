"""Compare saved helper graphs and evaluated geometry."""
import json

def compare(old_path, new_path):
    """Print changed helper graphs and evaluated positions."""
    a, b = json.load(open(old_path)), json.load(open(new_path))
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x == y:
            continue
        print("##", k)
        if not isinstance(x, dict) or not isinstance(y, dict) or "ERROR" in x or "ERROR" in y or k.startswith("eval"):
            print("  old:", str(x)[:300]); print("  new:", str(y)[:300]); continue
        for dk in sorted(set(x) | set(y)):
            gx, gy = x.get(dk), y.get(dk)
            if gx == gy: continue
            if gx is None or gy is None: print("  only in", "new" if gx is None else "old", dk); continue
            for part in ("nodes", "links", "interface"):
                ox, oy = gx[part], gy[part]
                if ox == oy: continue
                from collections import Counter
                cx, cy = Counter(map(str, ox)), Counter(map(str, oy))
                for s in (cx - cy): print("  -", dk, part, s[:260])
                for s in (cy - cx): print("  +", dk, part, s[:260])
