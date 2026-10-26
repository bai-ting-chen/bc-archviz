"""Check that the skill's folder structure, links and paths agree with SKILL.md's repository map.

Checks: every folder named in SKILL.md exists; every Markdown link and backtick path resolves;
every Python file compiles; every code folder with Python files appears in SKILL.md.
Run from anywhere: python scripts/workflow/structure_check.py (exit 1 on any problem).
"""
import glob
import os
import py_compile
import re
import sys

BS = chr(92)
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Print each problem and return a non-zero exit code when there are any."""
    os.chdir(SKILL)
    problems = []
    text = open('SKILL.md', encoding='utf-8').read()
    # 1. folders named in the repository map exist
    for path in set(re.findall(r'`((?:references|scripts)/[^`\s]*?)/?`', text)):
        if not os.path.exists(path):
            problems.append(f'SKILL.md names a missing path: {path}')
    # 2. Markdown links and backtick paths resolve
    for md in glob.glob('**/*.md', recursive=True):
        if md.startswith('.git'):
            continue
        body = open(md, encoding='utf-8').read()
        if md == 'MIGRATE.md':   # receiving-machine notes name the old paths on purpose
            continue
        base = os.path.dirname(md)
        for m in re.finditer(r'\]\(([^)#\s]+)(#[^)]*)?\)', body):
            target = m.group(1)
            if re.match(r'^(https?:|mailto:)', target):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                problems.append(f'{md}: broken link {target}')
        for m in re.finditer(r'`((?:scripts|references)[' + BS + '/][^`\\s]+)`', body):
            target = m.group(1).replace(BS, '/')
            if not os.path.exists(target):
                problems.append(f'{md}: broken path {target}')
    # 3. Python compiles
    for py in glob.glob('scripts/**/*.py', recursive=True):
        try:
            py_compile.compile(py, doraise=True)
        except py_compile.PyCompileError as exc:
            problems.append(f'{py}: does not compile ({exc.msg})')
        finally:
            pass
    # 4. every code folder with Python files is named in SKILL.md
    folders = {os.path.dirname(p).replace(os.sep, '/') for p in glob.glob('scripts/**/*.py', recursive=True)
               if '__pycache__' not in p}
    for folder in sorted(folders):
        if folder.endswith('/__pycache__'):
            continue
        if folder not in text and folder + '/' not in text and folder.rsplit('/', 1)[0] not in text:
            problems.append(f'code folder not in SKILL.md repository map: {folder}')
    for p in problems:
        print(p)
    print(f'{len(problems)} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
