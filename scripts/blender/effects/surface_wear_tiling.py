"""Deprecated: use effects.wear.tiling; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.tiling import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.tiling")


def __getattr__(name):
    return getattr(_owner, name)
