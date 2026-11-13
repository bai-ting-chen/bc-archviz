"""Deprecated: use effects.wear.chipping; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.chipping import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.chipping")


def __getattr__(name):
    return getattr(_owner, name)
