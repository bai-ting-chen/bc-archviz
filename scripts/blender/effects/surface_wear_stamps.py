"""Deprecated: use effects.wear.stamps; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.stamps import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.stamps")


def __getattr__(name):
    return getattr(_owner, name)
