"""Poly Haven endpoints, map formats and project-local library paths."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import core.projectpath as projectpath  # noqa: E402  (bpy-free; the same resolver archviz.library() uses)

API = "https://api.polyhaven.com"
UA = {"User-Agent": "ArchvizBlenderPipeline/0.1"}


def _project():
    """env ARCHVIZ_PROJECT, else projectpath.find_project from the working directory (a study
    stops the search at itself), else the working directory (library/ is created there)."""
    if os.environ.get("ARCHVIZ_PROJECT"):
        return os.environ["ARCHVIZ_PROJECT"]
    return projectpath.find_project([os.getcwd()]) or os.getcwd()


PROJECT = _project()
LIB = os.path.join(PROJECT, "library", "polyhaven")

# Poly Haven map key -> (local suffix, preferred formats). "arm" = AO/Rough/Metal packed in R/G/B.
TEX_MAPS = {
    "Diffuse": ("diff", ("jpg",)),
    "arm": ("arm", ("jpg",)),
    "nor_gl": ("nor_gl", ("jpg", "png")),
    "Displacement": ("disp", ("png", "jpg")),
}



