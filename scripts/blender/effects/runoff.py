"""Deprecated: use effects.wear.water_marks; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.water_marks import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.water_marks")


def __getattr__(name):
    return getattr(_owner, name)
