"""Regression check for the Blender helpers: build every material / node-group helper in a fresh
file and fingerprint each node graph by content (node types, settings, input values, links --
not names or layout), plus evaluated vertex positions of the GN wear groups.

  1. snapshot the current code:  git archive HEAD scripts | tar -x -C <dir>/old
  2. assets: a project folder whose library/ holds polyhaven/textures/{concrete_wall_009,
     coated_pine, gray_rocks} and polyhaven/hdris/kloppenheim_06_puresky (polyhaven_fetch.py)
     -- a throwaway copy, since albedo_material caches into meta.json
  3. blender -b --factory-startup --python helper_regression.py -- dump <scripts/blender> <project> <out.json>
     using each snapshot's own helper_regression.py and matching scripts/blender directory.
     A pre-package snapshot uses its pre-package runner; the current runner uses canonical materials modules.
  4. python helper_regression.py compare old.json new.json   -> only intended differences may print
"""

import os as _os, sys as _sys
_sys.path.append(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'controls'))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regression_compare import compare


def main():
    """Keep the host compare and Blender dump command lines intact."""
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif "--" in sys.argv and sys.argv[sys.argv.index("--") + 1] == "dump":
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "controls"))
        from regression_dump import dump
        SRC, HERE, OUT = sys.argv[sys.argv.index("--") + 2:][:3]
        dump(SRC, HERE, OUT)


if __name__ == '__main__':
    main()
