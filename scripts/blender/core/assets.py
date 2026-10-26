"""The project's asset library: which folder holds library/, and the meta.json of each asset.

Every asset folder carries a meta.json (Poly Haven fetch or a local/ asset). Paths resolve against
the project folder chosen by set_project(), else the ARCHVIZ_PROJECT variable, else the folder found
from the open .blend or the working directory (projectpath.find_project).
"""
import json
import os

import bpy

import core.projectpath as projectpath

# Code lives in the skill; assets live in a study's (or project's) library/ (polyhaven/, local/).
# The folder: set_project(path), else env ARCHVIZ_PROJECT, else projectpath.find_project from
# the open .blend, then the working directory (a study stops the search at itself, RULES AST_03).
_PROJECT = os.environ.get("ARCHVIZ_PROJECT")


def set_project(path):
    """Point library() at a study/project folder (else env ARCHVIZ_PROJECT, else found from the .blend / cwd)."""
    global _PROJECT
    _PROJECT = os.path.abspath(path)


def project_root():
    """The folder whose library/ holds the assets (see set_project and projectpath)."""
    if _PROJECT:
        return _PROJECT
    starts = [os.path.dirname(bpy.data.filepath)] if bpy.data.filepath else []
    found = projectpath.find_project(starts + [os.getcwd()])
    if found:
        return found
    raise RuntimeError("no project library/ found: call archviz.set_project(<study folder>)")


def library(*parts):
    """Path inside the project's library/, e.g. library("polyhaven", "hdris", hdri_id)."""
    return os.path.join(project_root(), "library", *parts)


def read_meta(folder):
    """An asset folder's meta.json (Poly Haven fetch or a local/ asset)."""
    with open(os.path.join(folder, "meta.json"), encoding="utf-8") as f:
        return json.load(f)


def write_meta(folder, meta):
    """Write an asset folder's meta.json (pair of read_meta)."""
    with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
