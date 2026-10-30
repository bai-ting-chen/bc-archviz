"""Resolve explicitly kept study milestones."""
import os
import re
import sys

from study_files import notes_path


def milestones(study, keep, apply=False):
    """Milestone .blend paths: --keep, else the study notes' `## Milestones`, else the newest .blend."""
    blends = sorted((f for f in os.listdir(study) if f.lower().endswith('.blend')),
                    key=lambda f: os.path.getmtime(os.path.join(study, f)))
    if not keep:
        notes = notes_path(study)
        if os.path.exists(notes):
            m = re.search(r'^## Milestones\s*$(.*?)(?=^## |\Z)', open(notes, encoding='utf-8').read(), re.M | re.S)
            if m:
                for line in m.group(1).splitlines():
                    ticked = re.findall(r'`([^`]+?\.blend)`', line)
                    plain = re.findall(r'(\S.*?\.blend)\b', re.sub(r'^\s*(?:[-*+]|\d+\.)\s+', '', line))
                    keep += ticked or plain[:1]
    keep = [k.strip() for k in keep]
    if not keep and apply:
        sys.exit(f'no milestones: list them under "## Milestones" in {os.path.basename(notes_path(study))} or pass --keep')
    keep = keep or blends[-1:]
    missing = [k for k in keep if k not in blends]
    if missing:
        sys.exit(f'milestone not found in study root: {missing}')
    return [os.path.join(study, k) for k in keep]
