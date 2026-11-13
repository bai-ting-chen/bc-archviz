"""Download the user's Quixel picks from fab-download.js links into <project>/library/local/<id>/.

Usage (MCP venv python; env ARCHVIZ_PROJECT=<study> as for polyhaven_fetch.py):
    python fab_fetch.py <links.json>
links.json is the list fabDownloadLinks() returned. Each pick is unzipped into its own folder
with a meta.json (the search row without the signed link); the zip is deleted afterwards.
"""
import json
import os
import sys
import zipfile

from polyhaven_config import PROJECT_ROOT
from polyhaven_http import _download

LOCAL_LIBRARY_DIR = os.path.join(PROJECT_ROOT, "library", "local")


def folder_name(pick):
    """The Megascans id, else the download file name without .zip (Megaplants have no id)."""
    return pick.get("id") or os.path.splitext(pick["file"])[0]


def unzip_inside(zip_path, dst):
    """Extract a zip, refusing any member that would land outside dst."""
    root = os.path.realpath(dst)
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not os.path.realpath(os.path.join(root, name)).startswith(root + os.sep):
                raise RuntimeError(f"{zip_path}: unsafe member {name}")
        z.extractall(root)


def fetch(pick):
    """Download one pick, check its size, unzip it and write its meta.json; return the folder."""
    dst = os.path.join(LOCAL_LIBRARY_DIR, folder_name(pick))
    zip_path = os.path.join(dst, pick["file"])
    _download(pick["url"], zip_path)
    if os.path.getsize(zip_path) != pick["size"]:
        raise RuntimeError(f"{pick['file']}: size {os.path.getsize(zip_path)} != {pick['size']}")
    unzip_inside(zip_path, dst)
    os.remove(zip_path)
    meta = {k: v for k, v in pick.items() if k not in ("url", "thumb")}
    meta["source"] = "Quixel on Fab"
    with open(os.path.join(dst, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return dst


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        picks = json.load(f)
    for pick in picks:
        print(fetch(pick))


if __name__ == "__main__":
    main()
