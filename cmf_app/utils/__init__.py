"""Utilitaires.

Lazy-loading avoids importing pandas-dependent helpers when a narrower
submodule such as utils.column_schema_manager is imported.
"""

from importlib import import_module

__all__ = [
    "CMFHelpers",
    "ChartHelpers",
    "ValidationHelpers",
]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module 'utils' has no attribute {name!r}")

    module = import_module("utils.helpers")
    value = getattr(module, name)
    globals()[name] = value
    return value
