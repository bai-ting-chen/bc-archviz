"""Regression check for the Blender helpers: build every material / node-group helper in a fresh
file and fingerprint each node graph by content (node types, settings, input values, links --
not names or layout), plus evaluated vertex positions of the GN wear groups.

  1. snapshot the current code:  git archive HEAD scripts | tar -x -C <dir>/old
  2. assets: a project folder whose library/ holds polyhaven/textures/{concrete_wall_009,
     coated_pine, gray_rocks}, polyhaven/hdris/kloppenheim_06_puresky and local/leakage_tdlbbd1c
     (polyhaven_fetch.py; the leak map is a Megascans download) -- a throwaway copy, since
     albedo_material caches into meta.json
  3. blender -b --factory-startup --python regress_helpers.py -- dump <scripts/blender> <project> <out.json>
     using each snapshot's own regress_helpers.py and matching scripts/blender directory.
     A pre-package snapshot uses its pre-package runner; the current runner uses canonical materials modules.
  4. python regress_helpers.py compare old.json new.json   -> only intended differences may print
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'controls')
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regress_compare import compare


def main():
    """Keep the host compare and Blender dump command lines intact."""
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif "--" in sys.argv and sys.argv[sys.argv.index("--") + 1] == "dump":
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "controls"))
        from regress_dump import dump
        SRC, HERE, OUT = sys.argv[sys.argv.index("--") + 2:][:3]
        dump(SRC, HERE, OUT)


if __name__ == '__main__':
    main()
