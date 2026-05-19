"""Services CMF.

This package uses lazy attribute loading so importing a specific submodule
like services.master_schema does not eagerly import the full service stack.
"""

from importlib import import_module

_EXPORTS = {
    "AuditService": ("services.audit_service", "AuditService"),
    "get_audit_service": ("services.audit_service", "get_audit_service"),
    "ValidationRules": ("services.validation_rules", "ValidationRules"),
    "validate_record": ("services.validation_rules", "validate_record"),
    "validate_source": ("services.validation_rules", "validate_source"),
    "CapacityEngine": ("services.capacity_engine", "CapacityEngine"),
    "IRepository": ("services.repository", "IRepository"),
    "SQLRepository": ("services.repository", "SQLRepository"),
    "RepositoryFactory": ("services.repository", "RepositoryFactory"),
    "IProjectRepository": ("services.project_repository", "IProjectRepository"),
    "IUserProjectRepository": ("services.project_repository", "IUserProjectRepository"),
    "JSONProjectRepository": ("services.project_repository", "JSONProjectRepository"),
    "JSONUserProjectRepository": ("services.project_repository", "JSONUserProjectRepository"),
    "ProjectRepositoryFactory": ("services.project_repository", "RepositoryFactory"),
    "ProjectContextService": ("services.project_context", "ProjectContextService"),
    "get_project_context_service": ("services.project_context", "get_project_context_service"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module 'services' has no attribute {name!r}")

    module_name, attribute_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
