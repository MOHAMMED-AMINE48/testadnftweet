"""Column schema helpers for CMF projects."""

import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from services.master_schema import (
    FIXED_COLUMNS,
    STANDARD_COLUMNS_BY_ROLE,
    STANDARD_COLUMNS_BY_KEY,
    STANDARD_COLUMNS_ORDER,
    get_column_label as get_master_column_label,
)


def _standard_columns_for_role(role: str) -> List[str]:
    role_upper = role.upper()
    return [
        column_key
        for column_key in STANDARD_COLUMNS_BY_ROLE.get(role_upper, [])
        if not STANDARD_COLUMNS_BY_KEY[column_key].get("is_auto", 0)
    ]


def _column_label(column_key: str) -> str:
    return get_master_column_label(column_key)


AVAILABLE_COLUMNS = {
    "buyer": {column_key: _column_label(column_key) for column_key in _standard_columns_for_role("BUYER")},
    "capacity_manager": {column_key: _column_label(column_key) for column_key in _standard_columns_for_role("CAPACITY_MANAGER")},
    "sqd": {column_key: _column_label(column_key) for column_key in _standard_columns_for_role("SQD")},
}


@dataclass
class ColumnSelection:
    """Represents the selected columns for each role."""

    buyer_columns: List[str]
    capacity_manager_columns: List[str]
    sqd_columns: List[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: Optional[str]) -> "ColumnSelection":
        if not json_str:
            return cls.default()
        try:
            data = json.loads(json_str)
            return cls(**data)
        except Exception:
            return cls.default()

    @classmethod
    def default(cls) -> "ColumnSelection":
        return cls(
            buyer_columns=_standard_columns_for_role("BUYER"),
            capacity_manager_columns=_standard_columns_for_role("CAPACITY_MANAGER"),
            sqd_columns=_standard_columns_for_role("SQD"),
        )


# Backward-compatible role-specific column maps.
def get_available_columns(role: str) -> Dict[str, str]:
    return AVAILABLE_COLUMNS.get(role.lower(), {})


def get_column_label(role: str, column_key: str) -> str:
    columns = get_available_columns(role)
    return columns.get(column_key, _column_label(column_key))


def get_all_available_columns(project_id: Optional[int] = None) -> Dict[str, str]:
    if project_id is None:
        result = {}
        for column_key in STANDARD_COLUMNS_ORDER:
            result[column_key] = _column_label(column_key)
        return result

    from repositories.project_column_repository_sqlite import ProjectColumnRepository

    column_repo = ProjectColumnRepository()
    result: Dict[str, str] = {}
    for column in column_repo.get_project_columns(project_id):
        result[column.column_name] = column.label or _column_label(column.column_name)
    return result


def validate_column_selection(selection: ColumnSelection) -> bool:
    available_buyer = set(AVAILABLE_COLUMNS["buyer"].keys())
    available_cm = set(AVAILABLE_COLUMNS["capacity_manager"].keys())
    available_sqd = set(AVAILABLE_COLUMNS["sqd"].keys())

    return (
        all(col in available_buyer for col in selection.buyer_columns)
        and all(col in available_cm for col in selection.capacity_manager_columns)
        and all(col in available_sqd for col in selection.sqd_columns)
    )


@dataclass
class ProjectColumnSchema:
    """Complete column configuration for a project (standard + custom)."""

    buyer_standard: List[str]
    buyer_custom: List[str]
    capacity_manager_standard: List[str]
    capacity_manager_custom: List[str]
    sqd_standard: List[str]
    sqd_custom: List[str]

    def get_buyer_columns(self) -> List[str]:
        return self.buyer_standard + self.buyer_custom

    def get_capacity_manager_columns(self) -> List[str]:
        return self.capacity_manager_standard + self.capacity_manager_custom

    def get_sqd_columns(self) -> List[str]:
        return self.sqd_standard + self.sqd_custom

    def get_columns_for_role(self, role: str) -> List[str]:
        role_key = role.lower()
        if role_key == "buyer":
            return self.get_buyer_columns()
        if role_key == "capacity_manager":
            return self.get_capacity_manager_columns()
        if role_key == "sqd":
            return self.get_sqd_columns()
        return []

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: Optional[str]) -> "ProjectColumnSchema":
        if not json_str:
            return cls.default()
        try:
            data = json.loads(json_str)
            if "buyer_standard" in data:
                return cls(**data)
            if "buyer_columns" in data:
                return cls(
                    buyer_standard=data.get("buyer_columns", []),
                    buyer_custom=[],
                    capacity_manager_standard=data.get("capacity_manager_columns", []),
                    capacity_manager_custom=[],
                    sqd_standard=data.get("sqd_columns", []),
                    sqd_custom=[],
                )
            return cls.default()
        except Exception:
            return cls.default()

    @classmethod
    def default(cls) -> "ProjectColumnSchema":
        return cls(
            buyer_standard=_standard_columns_for_role("BUYER"),
            buyer_custom=[],
            capacity_manager_standard=_standard_columns_for_role("CAPACITY_MANAGER"),
            capacity_manager_custom=[],
            sqd_standard=_standard_columns_for_role("SQD"),
            sqd_custom=[],
        )

    def add_custom_column(self, role: str, column_key: str, column_label: str) -> None:
        role_key = role.lower()
        column_key = column_key.strip().lower()
        if role_key == "buyer" and column_key not in self.buyer_custom:
            self.buyer_custom.append(column_key)
            AVAILABLE_COLUMNS["buyer"][column_key] = column_label
        elif role_key == "capacity_manager" and column_key not in self.capacity_manager_custom:
            self.capacity_manager_custom.append(column_key)
            AVAILABLE_COLUMNS["capacity_manager"][column_key] = column_label
        elif role_key == "sqd" and column_key not in self.sqd_custom:
            self.sqd_custom.append(column_key)
            AVAILABLE_COLUMNS["sqd"][column_key] = column_label


def get_filtered_columns_for_form(schema: ProjectColumnSchema, role: str) -> Dict[str, str]:
    role_key = role.lower()
    columns = schema.get_columns_for_role(role_key)
    available = AVAILABLE_COLUMNS.get(role_key, {})
    result: Dict[str, str] = {}

    for fixed_column in FIXED_COLUMNS:
        result[fixed_column] = _column_label(fixed_column)

    for column_key in columns:
        if column_key in result:
            continue
        if column_key in available:
            result[column_key] = available[column_key]
        elif column_key in FIXED_COLUMNS:
            result[column_key] = _column_label(column_key)
        else:
            result[column_key] = column_key.replace("_", " ").title()

    return result


def load_project_schema(cmf_schema_json: Optional[str]) -> ProjectColumnSchema:
    if not cmf_schema_json:
        return ProjectColumnSchema.default()

    try:
        data = json.loads(cmf_schema_json)
        if "buyer_standard" in data:
            return ProjectColumnSchema(**data)
        if "buyer_columns" in data:
            return ProjectColumnSchema(
                buyer_standard=data.get("buyer_columns", []),
                buyer_custom=[],
                capacity_manager_standard=data.get("capacity_manager_columns", []),
                capacity_manager_custom=[],
                sqd_standard=data.get("sqd_columns", []),
                sqd_custom=[],
            )
        return ProjectColumnSchema.default()
    except Exception:
        return ProjectColumnSchema.default()


def convert_column_selection_to_schema(selection: ColumnSelection) -> ProjectColumnSchema:
    return ProjectColumnSchema(
        buyer_standard=selection.buyer_columns,
        buyer_custom=[],
        capacity_manager_standard=selection.capacity_manager_columns,
        capacity_manager_custom=[],
        sqd_standard=selection.sqd_columns,
        sqd_custom=[],
    )
