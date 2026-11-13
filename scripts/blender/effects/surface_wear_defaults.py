"""Deprecated: use effects.wear.defaults; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.defaults import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.defaults")


def __getattr__(name):
    return getattr(_owner, name)
