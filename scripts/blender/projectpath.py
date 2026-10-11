"""Which folder's library/ a script reads and writes assets in (no bpy: also used by host tools).

Each study owns its assets (RULES 10c). Walking up from a start folder:
- a folder with its own library/ before any study folder -> that folder (a project, test scene);
- inside a study (a folder whose parent is named "studies") -> the study, even before its
  library/ exists, so downloads land there;
- a library/ above the study is used only when that library's legacy_studies.txt lists the
  study (studies made before per-study assets).
"""
import os

LEGACY_LIST = "legacy_studies.txt"


def is_study(folder):
    """A study folder: its parent folder is named 'studies'."""
    return os.path.basename(os.path.dirname(os.path.abspath(folder))).lower() == "studies"


def legacy_studies(project):
    """Study folder names listed in <project>/library/legacy_studies.txt (# comments allowed)."""
    p = os.path.join(project, "library", LEGACY_LIST)
    if not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as f:
        return {ln.split("#")[0].strip() for ln in f if ln.split("#")[0].strip()}


def find_project(starts):
    """Project folder for the first start that resolves (see module doc), else None."""
    for d in starts:
        if not d:
            continue
        d, study = os.path.abspath(d), None
        while True:
            if os.path.isdir(os.path.join(d, "library")):
                if study is None or d == study:
                    return d
                return d if os.path.basename(study) in legacy_studies(d) else study
            if study is None and is_study(d):
                study = d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
        if study:
            return study
    return None
