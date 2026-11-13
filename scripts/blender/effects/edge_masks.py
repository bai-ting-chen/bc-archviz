"""Deprecated: use effects.wear.mask_views; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.mask_views import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.mask_views")


def __getattr__(name):
    return getattr(_owner, name)
