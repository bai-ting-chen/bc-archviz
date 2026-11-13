"""Download Poly Haven (CC0) HDRIs and PBR textures into a study's library/polyhaven.
Each study owns its assets (RULES AST_03): run with env ARCHVIZ_PROJECT=<study folder>.

Assets are CC0. Data comes from the live API at api.polyhaven.com -- Powered by Poly Haven.

Usage:
    python polyhaven_fetch.py hdri  <id> [<id> ...] [--resolution 4k]
    python polyhaven_fetch.py tex   <id> [<id> ...] [--resolution 2k]
    python polyhaven_fetch.py search <hdris|textures> <category> [--top 10]
"""
import argparse
from polyhaven_config import API_BASE_URL, REQUEST_HEADERS, PROJECT_ROOT, LIBRARY_DIR, TEXTURE_MAP_FORMATS, project_paths, _project
from polyhaven_http import _get, _md5, _download
from polyhaven_metadata import _write_meta
from polyhaven_hdri import fetch_hdri
from polyhaven_texture import fetch_texture
from polyhaven_search import search


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["hdri", "tex", "search"])
    p.add_argument("asset_ids", nargs="+")
    p.add_argument("--resolution", dest='resolution')
    p.add_argument("--top", type=int, default=10)
    a = p.parse_args()
    if a.command == "search":
        search(a.asset_ids[0], a.asset_ids[1], a.top)
    elif not project_paths.is_study(PROJECT_ROOT):
        print(f"NOTE: downloading into {LIBRARY_DIR}, which is not a study's library (RULES AST_03). "
              f"Set ARCHVIZ_PROJECT=<study folder> unless this is meant.")
    for i in a.asset_ids if a.command != "search" else ():
        try:
            (fetch_hdri if a.command == "hdri" else fetch_texture)(i, a.resolution or ("4k" if a.command == "hdri" else "2k"))
        except Exception as ex:
            print(f"FAILED {i}: {ex}")


if __name__ == '__main__':
    main()
