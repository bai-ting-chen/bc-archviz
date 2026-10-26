"""Acquire one HDRI into the current project library."""
import os
from polyhaven_config import API, LIB
from polyhaven_http import _get, _download
from polyhaven_meta import _write_meta

def fetch_hdri(asset_id, res):
    """Download an HDRI at the requested resolution and save its metadata."""
    files = _get(f"{API}/files/{asset_id}")["hdri"][res]["hdr"]
    folder = os.path.join(LIB, "hdris", asset_id)
    dst = os.path.join(folder, f"{asset_id}_{res}.hdr")
    status = _download(files["url"], dst, files.get("md5"))
    _write_meta(folder, asset_id, {"res": res, "file": os.path.basename(dst)})
    print(f"hdri {asset_id} {res}: {status}")
