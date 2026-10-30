"""Check that the skill's folder structure, links and paths agree with SKILL.md's repository map.

Checks: every folder named in SKILL.md exists; every Markdown link and backtick path resolves;
every Python file compiles; every code folder with Python files appears in SKILL.md; no two
reference files reach each other by links (a loop); every #anchor names a heading.
Run from anywhere: python scripts/workflow/structure_check.py (exit 1 on any problem).
"""
import glob
import os
import py_compile
import re
import sys

BS = chr(92)
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ALWAYS_LOADED = {'SKILL.md', 'RULES.md'}   # links back to these close no loop: they are read first anyway


def prose(md):
    """The file's text without fenced code blocks: links and headings there are not real."""
    return re.sub(r'^```.*?^```', '', open(md, encoding='utf-8').read(), flags=re.M | re.S)


def link_graph():
    """Markdown file -> the set of Markdown files it links to (no self-links, no links into ALWAYS_LOADED)."""
    graph = {}
    for md in glob.glob('**/*.md', recursive=True):
        if md.startswith('.git') or md in ('MIGRATE.md', 'README.md'):
            continue
        base = os.path.dirname(md)
        body = prose(md)
        targets = set()
        for m in re.finditer(r'\]\(([^)#\s]+\.md)(#[^)]*)?\)', body):
            target = os.path.relpath(os.path.normpath(os.path.join(base, m.group(1))))
            if target != md and target not in ALWAYS_LOADED:
                targets.add(target)
        graph[md] = targets
    return graph


def reference_loops():
    """One problem per group of files that can reach each other by links (A -> B -> ... -> A)."""
    graph = link_graph()
    order, low, stack, on_stack, groups = {}, {}, [], set(), []

    def visit(v):                                      # Tarjan's strongly connected components
        order[v] = low[v] = len(order)
        stack.append(v)
        on_stack.add(v)
        for w in graph[v]:
            if w not in graph:
                continue
            if w not in order:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], order[w])
        if low[v] == order[v]:
            group = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                group.append(w)
                if w == v:
                    break
            if len(group) > 1:
                groups.append(sorted(group))

    for v in sorted(graph):
        if v not in order:
            visit(v)
    problems = []
    for group in groups:
        links = [f'{a} -> {b}' for a in group for b in sorted(graph[a]) if b in group]
        problems.append(('reference loop between ' + ', '.join(group)
                         + '\n    ' + '\n    '.join(links)).replace(BS, '/'))
    return problems


def heading_slug(heading):
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces as hyphens."""
    return re.sub(r'[^\w\- ]', '', heading.strip().lower()).replace(' ', '-')


def broken_anchors():
    """One problem per link whose #anchor matches no heading of the file it points to."""
    files = [md for md in glob.glob('**/*.md', recursive=True) if not md.startswith('.git') and md != 'MIGRATE.md']
    slugs = {os.path.normpath(md): {heading_slug(h) for h in re.findall(r'^#+\s+(.*)$', prose(md), re.M)}
             for md in files}
    problems = []
    for md in files:
        for m in re.finditer(r'\]\(([^)#\s]*)#([^)\s]+)\)', prose(md)):
            target = os.path.normpath(os.path.join(os.path.dirname(md), m.group(1))) if m.group(1) else os.path.normpath(md)
            if target in slugs and m.group(2) not in slugs[target]:
                problems.append(f'{md}: no heading for #{m.group(2)} in {m.group(1) or md}'.replace(BS, '/'))
    return problems


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
    # 5. no reference loops between skill files (reference-format.md)
    problems += reference_loops()
    # 6. every #anchor names a heading in its target file
    problems += broken_anchors()
    for p in problems:
        print(p)
    print(f'{len(problems)} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
