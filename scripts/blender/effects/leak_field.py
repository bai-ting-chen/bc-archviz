"""Deprecated: use effects.wear.leak_field; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.leak_field import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.leak_field")


def __getattr__(name):
    return getattr(_owner, name)
