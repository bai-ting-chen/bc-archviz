"""Download Poly Haven (CC0) HDRIs and PBR textures into a study's library/polyhaven.
Each study owns its assets (RULES AST_03): run with env ARCHVIZ_PROJECT=<study folder>.

Assets are CC0. Data comes from the live API at api.polyhaven.com -- Powered by Poly Haven.

Usage:
    python polyhaven_fetch.py hdri  <id> [<id> ...] [--res 4k]
    python polyhaven_fetch.py tex   <id> [<id> ...] [--res 2k]
    python polyhaven_fetch.py search <hdris|textures> <category> [--top 10]
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender"))
import projectpath  # noqa: E402  (bpy-free; the same resolver archviz.library() uses)

API = "https://api.polyhaven.com"
UA = {"User-Agent": "ArchvizBlenderPipeline/0.1"}


def _project():
    """env ARCHVIZ_PROJECT, else projectpath.find_project from the working directory (a study
    stops the search at itself), else the working directory (library/ is created there)."""
    if os.environ.get("ARCHVIZ_PROJECT"):
        return os.environ["ARCHVIZ_PROJECT"]
    return projectpath.find_project([os.getcwd()]) or os.getcwd()


PROJECT = _project()
LIB = os.path.join(PROJECT, "library", "polyhaven")

# Poly Haven map key -> (local suffix, preferred formats). "arm" = AO/Rough/Metal packed in R/G/B.
TEX_MAPS = {
    "Diffuse": ("diff", ("jpg",)),
    "arm": ("arm", ("jpg",)),
    "nor_gl": ("nor_gl", ("jpg", "png")),
    "Displacement": ("disp", ("png", "jpg")),
}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        return json.load(r)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _download(url, dst, md5=None):
    if os.path.exists(dst) and md5 and _md5(dst) == md5:
        return "cached"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    if md5 and _md5(tmp) != md5:
        os.remove(tmp)
        raise RuntimeError("md5 mismatch: " + url)
    os.replace(tmp, dst)
    return "ok"


def _write_meta(folder, asset_id, extra):
    info = _get(f"{API}/info/{asset_id}")
    meta = {
        "id": asset_id, "name": info.get("name"), "categories": info.get("categories"),
        "tags": info.get("tags"), "authors": info.get("authors"), "license": "CC0",
        "source": f"https://polyhaven.com/a/{asset_id}", **extra,
    }
    if "dimensions" in info:  # textures: real-world size in mm, used for UV scale
        meta["dimensions_mm"] = info["dimensions"]
    if "whitebalance" in info:
        meta["whitebalance"] = info["whitebalance"]
    with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def fetch_hdri(asset_id, res):
    files = _get(f"{API}/files/{asset_id}")["hdri"][res]["hdr"]
    folder = os.path.join(LIB, "hdris", asset_id)
    dst = os.path.join(folder, f"{asset_id}_{res}.hdr")
    status = _download(files["url"], dst, files.get("md5"))
    _write_meta(folder, asset_id, {"res": res, "file": os.path.basename(dst)})
    print(f"hdri {asset_id} {res}: {status}")


def fetch_tex(asset_id, res):
    files = _get(f"{API}/files/{asset_id}")
    folder = os.path.join(LIB, "textures", asset_id)
    maps = {}
    for key, (suffix, fmts) in TEX_MAPS.items():
        entry = files.get(key, {}).get(res, {})
        fmt = next((f for f in fmts if f in entry), None)
        if not fmt:
            continue
        dst = os.path.join(folder, f"{asset_id}_{suffix}_{res}.{fmt}")
        _download(entry[fmt]["url"], dst, entry[fmt].get("md5"))
        maps[suffix] = os.path.basename(dst)
    _write_meta(folder, asset_id, {"res": res, "maps": maps})
    print(f"tex  {asset_id} {res}: {sorted(maps)}")


def search(kind, category, top):
    d = _get(f"{API}/assets?t={kind}&c={urllib.parse.quote(category)}")
    for k, v in sorted(d.items(), key=lambda kv: -kv[1].get("download_count", 0))[:top]:
        print(f"{k:40s} {v['name']}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["hdri", "tex", "search"])
    p.add_argument("ids", nargs="+")
    p.add_argument("--res")
    p.add_argument("--top", type=int, default=10)
    a = p.parse_args()
    if a.cmd == "search":
        search(a.ids[0], a.ids[1], a.top)
    elif not projectpath.is_study(PROJECT):
        print(f"NOTE: downloading into {LIB}, which is not a study's library (RULES AST_03). "
              f"Set ARCHVIZ_PROJECT=<study folder> unless this is meant.")
    for i in a.ids if a.cmd != "search" else ():
        try:
            (fetch_hdri if a.cmd == "hdri" else fetch_tex)(i, a.res or ("4k" if a.cmd == "hdri" else "2k"))
        except Exception as ex:
            print(f"FAILED {i}: {ex}")


if __name__ == "__main__":
    main()
