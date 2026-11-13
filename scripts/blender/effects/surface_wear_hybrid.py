"""Deprecated: use effects.wear.hybrid; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.hybrid import *
from effects.wear.scratches import scratch_hybrid
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.hybrid")


def __getattr__(name):
    return getattr(_owner, name)
