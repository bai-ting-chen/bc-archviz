"""Print popular Poly Haven assets within one category."""
import urllib.parse
from polyhaven_config import API
from polyhaven_http import _get

def search(kind, category, top):
    """Print the most-downloaded assets matching a kind and category."""
    d = _get(f"{API}/assets?t={kind}&c={urllib.parse.quote(category)}")
    for k, v in sorted(d.items(), key=lambda kv: -kv[1].get("download_count", 0))[:top]:
        print(f"{k:40s} {v['name']}")
