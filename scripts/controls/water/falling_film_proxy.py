"""Check the transformed wet proxy in wall-local coordinates."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import numpy as np

def check_proxy(proxy, lip, setup, checks):
    """Check wet-proxy points remain on the wall face."""
    pv = np.empty(len(proxy.data.vertices) * 3, np.float32); proxy.data.vertices.foreach_get('co', pv)
    pw = np.c_[pv.reshape(-1, 3), np.ones(len(pv) // 3)] @ np.array(proxy.matrix_world).T
    _, o = lip.local(pw[:, :3]); checks['wet proxy on the wall face'] = bool(len(o)) and float(np.abs(o - setup.wet.gap).max()) < 1e-4
