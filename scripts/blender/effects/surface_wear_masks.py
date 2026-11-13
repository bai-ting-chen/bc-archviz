"""Deprecated: use effects.wear.masks; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.masks import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.masks")


def __getattr__(name):
    return getattr(_owner, name)
