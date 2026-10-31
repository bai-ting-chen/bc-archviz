"""Read scene references without saving: blender -b scene.blend --python blend_refs.py -- --out refs.json."""
import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reference_paths import references, files_of


def main():
    """Write sorted raw reference paths and their concrete files without changing the scene."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    rows = [[type(owner).__name__, attr, getattr(owner, attr), files_of(owner, path)]
            for owner, attr, path in references()]
    with open(args.out, 'w', encoding='utf-8') as stream:
        json.dump(sorted(rows, key=json.dumps), stream, indent=2)


if __name__ == '__main__':
    main()
