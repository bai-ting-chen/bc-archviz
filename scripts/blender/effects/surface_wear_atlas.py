"""Deprecated: use effects.wear.atlas; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.atlas import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.atlas")


def __getattr__(name):
    return getattr(_owner, name)
