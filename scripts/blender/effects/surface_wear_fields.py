"""Deprecated: use effects.wear.patterns; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.patterns import *
from effects.wear.scratches import scratches_field as _scratches
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.patterns")


def __getattr__(name):
    return getattr(_owner, name)
