"""Acquire one HDRI into the current project library."""
import os
from polyhaven_config import API_BASE_URL, LIBRARY_DIR
from polyhaven_http import _get, _download
from polyhaven_metadata import _write_meta

def fetch_hdri(asset_id, resolution):
    """Download an HDRI at the requested resolution and save its metadata."""
    files = _get(f"{API_BASE_URL}/files/{asset_id}")["hdri"][resolution]["hdr"]
    folder = os.path.join(LIBRARY_DIR, "hdris", asset_id)
    dst = os.path.join(folder, f"{asset_id}_{resolution}.hdr")
    status = _download(files["url"], dst, files.get("md5"))
    _write_meta(folder, asset_id, {"resolution": resolution, "file": os.path.basename(dst)})
    print(f"hdri {asset_id} {resolution}: {status}")
