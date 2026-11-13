"""Deprecated: use effects.wear.concrete_shading; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.concrete_shading import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.concrete_shading")


def __getattr__(name):
    return getattr(_owner, name)
