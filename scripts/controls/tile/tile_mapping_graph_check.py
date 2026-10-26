"""Deterministic tile_mapping graph/geometry baseline; pass output JSON after --."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from material_graph_cases import run

run("tile_mapping")
