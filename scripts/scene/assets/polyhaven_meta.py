"""Write the source and physical metadata for one downloaded asset."""
import os
import json
from polyhaven_config import API
from polyhaven_http import _get

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
