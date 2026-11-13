"""Acquire the supported PBR maps for one texture asset."""
import os
from polyhaven_config import API_BASE_URL, LIBRARY_DIR, TEXTURE_MAP_FORMATS
from polyhaven_http import _get, _download
from polyhaven_metadata import _write_meta

def fetch_texture(asset_id, res):
    """Download the available PBR maps and save their real-scale metadata."""
    files = _get(f"{API_BASE_URL}/files/{asset_id}")
    folder = os.path.join(LIBRARY_DIR, "textures", asset_id)
    maps = {}
    for key, (suffix, fmts) in TEXTURE_MAP_FORMATS.items():
        entry = files.get(key, {}).get(res, {})
        fmt = next((f for f in fmts if f in entry), None)
        if not fmt:
            continue
        dst = os.path.join(folder, f"{asset_id}_{suffix}_{res}.{fmt}")
        _download(entry[fmt]["url"], dst, entry[fmt].get("md5"))
        maps[suffix] = os.path.basename(dst)
    _write_meta(folder, asset_id, {"res": res, "maps": maps})
    print(f"tex  {asset_id} {res}: {sorted(maps)}")
