"""Download Poly Haven (CC0) HDRIs and PBR textures into a study's library/polyhaven.
Each study owns its assets (RULES AST_03): run with env ARCHVIZ_PROJECT=<study folder>.

Assets are CC0. Data comes from the live API at api.polyhaven.com -- Powered by Poly Haven.

Usage:
    python polyhaven_fetch.py hdri  <id> [<id> ...] [--res 4k]
    python polyhaven_fetch.py tex   <id> [<id> ...] [--res 2k]
    python polyhaven_fetch.py search <hdris|textures> <category> [--top 10]
"""
import argparse
from polyhaven_config import API, UA, PROJECT, LIB, TEX_MAPS, projectpath, _project
from polyhaven_http import _get, _md5, _download
from polyhaven_meta import _write_meta
from polyhaven_hdri import fetch_hdri
from polyhaven_texture import fetch_tex
from polyhaven_search import search


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


if __name__ == '__main__':
    main()
