"""Deprecated: use effects.wear.dirt; thin re-export marked for removal (see MIGRATE.md)."""
from effects.wear.dirt import *
from effects.wear.edge_profile import *
from effects.wear.edge_profile import edge_vertex_join
from importlib import import_module as _import_module
_owner = _import_module("effects.wear.dirt")


def __getattr__(name):
    return getattr(_owner, name)
