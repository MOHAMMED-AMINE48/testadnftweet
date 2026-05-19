"""Modèles de données CMF.

Lazy-loading keeps importing a single model module from triggering optional
pandas-heavy dependencies in unrelated model modules.
"""

from importlib import import_module

__all__ = [
    "CMFRecord",
    "CapacitySource",
    "AuditLog",
    "ValidationResult",
    "ImportResult",
    "CapacityCalculationMethod",
    "Project",
    "UserProjectRole",
    "ProjectContext",
    "ProjectStatus",
]

_MODEL_EXPORTS = {
    "CMFRecord": ("models.cmf_schema", "CMFRecord"),
    "CapacitySource": ("models.cmf_schema", "CapacitySource"),
    "AuditLog": ("models.cmf_schema", "AuditLog"),
    "ValidationResult": ("models.cmf_schema", "ValidationResult"),
    "ImportResult": ("models.cmf_schema", "ImportResult"),
    "CapacityCalculationMethod": ("models.cmf_schema", "CapacityCalculationMethod"),
    "Project": ("models.project_schema", "Project"),
    "UserProjectRole": ("models.project_schema", "UserProjectRole"),
    "ProjectContext": ("models.project_schema", "ProjectContext"),
    "ProjectStatus": ("models.project_schema", "ProjectStatus"),
}


def __getattr__(name):
    if name not in _MODEL_EXPORTS:
        raise AttributeError(f"module 'models' has no attribute {name!r}")

    module_name, attribute_name = _MODEL_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
