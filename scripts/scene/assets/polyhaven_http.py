"""Poly Haven JSON requests and checksum-verified atomic downloads."""
import hashlib
import json
import os
import urllib.request
from polyhaven_config import UA

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
