"""Deprecated: use effects.wear.wear_locations; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.wear_locations import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.wear_locations")


def __getattr__(name):
    return getattr(_owner, name)
