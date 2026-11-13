"""Deprecated: use effects.wear.crack_ribbon; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.crack_ribbon import *
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.crack_ribbon")


def __getattr__(name):
    return getattr(_owner, name)
